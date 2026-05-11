"""HotelAgent — Scheduler: Zeitgesteuerte Ausfuehrung von Automationen."""

import threading
import time

import schedule
from loguru import logger
from rich.console import Console

from scripts.automation_manager import get_scheduled_automations, run_automation

console = Console()

# Globaler Stop-Flag
_stop_event = threading.Event()
_scheduler_thread: threading.Thread | None = None


def _parse_schedule(trigger: dict):
    """Schedule-Job aus Trigger-Config erstellen.

    Unterstuetzte Formate:
    - schedule_time: "08:00" (taegliche Ausfuehrung)
    - schedule_days: ["monday", "tuesday", ...] + schedule_time
    - schedule_days leer + schedule_time -> taeglich
    """
    time_str = trigger.get("schedule_time", "08:00")
    days = trigger.get("schedule_days", [])

    if not days:
        # Taeglich
        return schedule.every().day.at(time_str)
    else:
        # Bestimmte Wochentage
        jobs = []
        day_map = {
            "monday": schedule.every().monday,
            "tuesday": schedule.every().tuesday,
            "wednesday": schedule.every().wednesday,
            "thursday": schedule.every().thursday,
            "friday": schedule.every().friday,
            "saturday": schedule.every().saturday,
            "sunday": schedule.every().sunday,
        }
        for day in days:
            day_lower = day.lower()
            if day_lower in day_map:
                jobs.append(day_map[day_lower].at(time_str))
        return jobs


def _job_wrapper(automation_name: str):
    """Wrapper fuer Automation-Ausfuehrung im Scheduler."""
    try:
        logger.info(f"Scheduler: Starte Automation '{automation_name}'")
        console.print(f"[dim]Scheduler: Starte '{automation_name}'...[/dim]")
        result = run_automation(automation_name)
        console.print(f"[green]Scheduler: '{automation_name}' — {result}[/green]")
    except Exception as e:
        logger.error(f"Scheduler: '{automation_name}' fehlgeschlagen: {e}")
        console.print(f"[red]Scheduler: '{automation_name}' — Fehler: {e}[/red]")


def load_scheduled_jobs():
    """Alle zeitgesteuerten Automationen als Jobs laden."""
    schedule.clear()
    automations = get_scheduled_automations()

    for auto in automations:
        name = auto["name"]
        trigger = auto.get("trigger", {})
        result = _parse_schedule(trigger)

        if isinstance(result, list):
            for job in result:
                job.do(_job_wrapper, automation_name=name)
        else:
            result.do(_job_wrapper, automation_name=name)

        days = trigger.get("schedule_days", [])
        time_str = trigger.get("schedule_time", "?")
        day_info = ", ".join(days) if days else "taeglich"
        logger.info(f"Scheduler: Job '{name}' geladen — {day_info} um {time_str}")

    return len(automations)


def _run_loop():
    """Scheduler-Loop (laeuft in separatem Thread oder Vordergrund)."""
    while not _stop_event.is_set():
        schedule.run_pending()
        time.sleep(30)


def start(background: bool = False):
    """Scheduler starten.

    Args:
        background: True = in Hintergrund-Thread, False = blockierend im Vordergrund.
    """
    global _scheduler_thread

    _stop_event.clear()
    count = load_scheduled_jobs()

    if count == 0:
        console.print("[yellow]Keine zeitgesteuerten Automationen vorhanden.[/yellow]")
        return

    console.print(f"[bold cyan]Scheduler gestartet — {count} Job(s) geladen.[/bold cyan]")

    # Naechste Ausfuehrungen anzeigen
    for job in schedule.get_jobs():
        console.print(f"  [dim]Naechste Ausfuehrung: {job.next_run}[/dim]")

    if background:
        _scheduler_thread = threading.Thread(target=_run_loop, daemon=True)
        _scheduler_thread.start()
        logger.info("Scheduler im Hintergrund gestartet.")
    else:
        console.print("[dim]Scheduler laeuft (Ctrl+C zum Beenden)...[/dim]\n")
        try:
            _run_loop()
        except KeyboardInterrupt:
            stop()


def stop():
    """Scheduler stoppen."""
    _stop_event.set()
    schedule.clear()
    console.print("[dim]Scheduler gestoppt.[/dim]")
    logger.info("Scheduler gestoppt.")


def is_running() -> bool:
    """Pruefen ob der Scheduler laeuft."""
    return _scheduler_thread is not None and _scheduler_thread.is_alive()


def reload_jobs():
    """Jobs neu laden (z.B. nach Aenderung an Automationen)."""
    count = load_scheduled_jobs()
    logger.info(f"Scheduler: {count} Job(s) neu geladen.")
    return count
