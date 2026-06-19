import psutil
import json
import socket
import datetime
from time import sleep
from rich import print
from rich.console import Console
from rich.table import Table
from rich.live import Live

def get_metrics():

    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')
    host_name = socket.gethostname()
    timestamp = datetime.datetime.now().strftime("%H:%M:%S | %d-%m-%Y")
    
    metrics = {
            "host_name": host_name,
            "timestamp": timestamp,
            "cpu": {
                "usage_percent": cpu_usage
            },
            "memory": {
                "total_gb": round(memory_usage.total / (1024 ** 3), 2),
                "available_gb": round(memory_usage.available / (1024 ** 3), 2),
                "used_gb": round(memory_usage.used / (1024 ** 3), 2),
                "percent": memory_usage.percent
            },
            "disk": {
                "total_gb": round(disk_usage.total / (1024 ** 3), 2),
                "used_gb": round(disk_usage.used / (1024 ** 3), 2),
                "free_gb": round(disk_usage.free / (1024 ** 3), 2),
                "percent": disk_usage.percent
            }
        }

    
    return metrics


def generate_table(metrics):
    console = Console()
    
    nom_machine = metrics["host_name"]
    heure_releve = metrics["timestamp"]

    table = Table(
        title=f"System Dashboard - [bold blue]{nom_machine}[/bold blue]",
        caption=f"Last refresh\n{heure_releve}",
        caption_style="dim"
    )

    table.add_column("Composant", justify="left", style="cyan", no_wrap=True)
    table.add_column("Utilisation", justify="right", style="magenta")
    table.add_column("Statut", justify="center")

    # Logique d'affichage pour le CPU
    cpu_usage = metrics["cpu"]["usage_percent"]
    if cpu_usage < 60:
        cpu_status = "[green]OK[/green]"
    elif cpu_usage < 80:
        cpu_status = "[yellow]Avertissement[/yellow]"
    else:
        cpu_status = "[red]Critique[/red]"
        
    table.add_row("CPU", f"{cpu_usage}%", cpu_status)

    # Logique d'affichage pour la mémoire
    memory_usage = metrics["memory"]["percent"]
    if memory_usage < 60:
        memory_status = "[green]OK[/green]"
    elif memory_usage < 80:
        memory_status = "[yellow]Avertissement[/yellow]"
    else:
        memory_status = "[red]Critique[/red]"

    table.add_row("Memory", f"{memory_usage}%", memory_status)

    # Logique d'affichage pour le disque
    disk_usage = metrics["disk"]["percent"]
    if disk_usage < 60:
        disk_status = "[green]OK[/green]"
    elif disk_usage < 80:
        disk_status = "[yellow]Avertissement[/yellow]"
    else:
        disk_status = "[red]Critique[/red]"

    table.add_row("Disk (/)", f"{disk_usage}%", disk_status)

    return table

if __name__ == "__main__":
    initial_metrics = get_metrics()
    
    with Live(generate_table(initial_metrics), refresh_per_second=4) as live:
        try:
            while True:
                new_metrics = get_metrics() 
                live.update(generate_table(new_metrics))
        except KeyboardInterrupt:
            pass