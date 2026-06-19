import psutil
import socket
import datetime
import time
import platform
import ipaddress
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.live import Live

def get_os_name():
    try:
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('PRETTY_NAME='):
                    return line.split('=')[1].strip().strip('"')
    except Exception:
        pass
    return platform.system()

def get_cpu_model():
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'model name' in line:
                    return line.split(':')[1].strip()
    except Exception:
        pass
    return platform.processor()

def get_network_info():
    ip = "127.0.0.1"
    mask = "255.0.0.0"
    cidr = "8"
    try:
        # Résolution de l'IP de routage local
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        
        # Corrélation pour trouver le masque et calcul du CIDR
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.address == ip:
                    mask = addr.netmask
                    cidr = str(ipaddress.IPv4Network(f'0.0.0.0/{mask}').prefixlen)
                    break
    except Exception:
        pass
    return ip, mask, cidr

def get_metrics():
    # Données dynamiques d'utilisation
    cpu_usage = psutil.cpu_percent(interval=1)
    
    # Extraction de la fréquence (Gestion de l'indisponibilité sur certaines VM)
    cpu_freq = psutil.cpu_freq()
    freq_str = f"{round(cpu_freq.current / 1000, 2)} GHz" if cpu_freq else "N/A"
    
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage('/')
    
    # Données d'identité et réseau
    host_name = socket.gethostname()
    local_ip, subnet_mask, cidr = get_network_info()
    timestamp = datetime.datetime.now().strftime("%H:%M:%S | %d-%m-%Y")
    
    # Données système
    os_name = get_os_name()
    kernel_version = platform.release()
    cpu_model = get_cpu_model()
    
    # Calcul de l'uptime
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    uptime_str = str(datetime.timedelta(seconds=uptime_seconds))

    # Structuration du Payload
    metrics = {
        "identity": {
            "host_name": host_name,
            "os": os_name,
            "kernel": kernel_version,
            "cpu_model": cpu_model,
            "uptime": uptime_str,
            "timestamp": timestamp
        },
        "network": {
            "local_ip": local_ip,
            "subnet_mask": subnet_mask,
            "cidr": cidr
        },
        "cpu": {
            "usage_percent": cpu_usage,
            "clock_speed": freq_str
        },
        "memory": {
            "total_gb": round(memory.total / (1024 ** 3), 2),
            "used_gb": round(memory.used / (1024 ** 3), 2),
            "percent": memory.percent
        },
        "swap": {
            "total_gb": round(swap.total / (1024 ** 3), 2),
            "used_gb": round(swap.used / (1024 ** 3), 2),
            "percent": swap.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "percent": disk.percent
        }
    }
    
    return metrics

def generate_dashboard(metrics):
    ident = metrics["identity"]
    net = metrics["network"]

    # --- Composant 1 : Panneau d'Information Statique ---
    info_text = (
        f"[cyan]OS:[/cyan] {ident['os']}  |  [cyan]Kernel:[/cyan] {ident['kernel']}  |  [cyan]Uptime:[/cyan] {ident['uptime']}\n"
        f"[cyan]CPU:[/cyan] {ident['cpu_model']}\n"
        f"[cyan]Network:[/cyan] {net['local_ip']}/{net['cidr']} ({net['subnet_mask']})"
    )
    
    info_panel = Panel(
        info_text, 
        title=f"[bold blue]{ident['host_name']}[/bold blue]", 
        expand=False, 
        border_style="blue"
    )

    # --- Composant 2 : Tableau de Télémétrie Dynamique ---
    table = Table(caption=f"Last refresh\n{ident['timestamp']}", caption_style="dim")

    table.add_column("Component", justify="left", style="cyan", no_wrap=True)
    table.add_column("Values", justify="left", style="magenta")
    table.add_column("Usage %", justify="right", style="magenta")
    table.add_column("Status", justify="center")

    # CPU
    cpu = metrics["cpu"]
    cpu_stat = "[green]OK[/green]" if cpu["usage_percent"] < 60 else "[yellow]Warn[/yellow]" if cpu["usage_percent"] < 80 else "[red]Crit[/red]"
    table.add_row("CPU", cpu["clock_speed"], f"{cpu['usage_percent']}%", cpu_stat)

    # Memory
    ram = metrics["memory"]
    ram_stat = "[green]OK[/green]" if ram["percent"] < 60 else "[yellow]Warn[/yellow]" if ram["percent"] < 80 else "[red]Crit[/red]"
    table.add_row("Memory", f"{ram['used_gb']} GB / {ram['total_gb']} GB", f"{ram['percent']}%", ram_stat)

    # Swap
    swap = metrics["swap"]
    swap_stat = "[green]OK[/green]" if swap["percent"] < 60 else "[yellow]Warn[/yellow]" if swap["percent"] < 80 else "[red]Crit[/red]"
    table.add_row("Swap", f"{swap['used_gb']} GB / {swap['total_gb']} GB", f"{swap['percent']}%", swap_stat)

    # Disk
    disk = metrics["disk"]
    disk_stat = "[green]OK[/green]" if disk["percent"] < 60 else "[yellow]Warn[/yellow]" if disk["percent"] < 80 else "[red]Crit[/red]"
    table.add_row("Disk (/)", f"{disk['used_gb']} GB / {disk['total_gb']} GB", f"{disk['percent']}%", disk_stat)

    return Group(info_panel, table)

if __name__ == "__main__":
    initial_metrics = get_metrics()
    
    with Live(generate_dashboard(initial_metrics), refresh_per_second=4) as live:
        try:
            while True:
                new_metrics = get_metrics() 
                live.update(generate_dashboard(new_metrics))
        except KeyboardInterrupt:
            pass