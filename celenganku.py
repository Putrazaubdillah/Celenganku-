import os
import json
import threading
import sys
import termios
import tty
from time import sleep, time
from rich.live import Live
from datetime import datetime
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress
from rich.box import ROUNDED
from rich.align import Align
from rich.layout import Layout
from rich.text import Text

console = Console()
DATA_DIR = "celengan_data"
os.makedirs(DATA_DIR, exist_ok=True)
stop_thread = False

def list_tabungan():
    return [f[:-5] for f in os.listdir(DATA_DIR) if f.endswith(".json")]

def read_tabungan(name):
    with open(f"{DATA_DIR}/{name}.json") as f:
        return json.load(f)

def write_tabungan(name, data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filepath = f"{DATA_DIR}/{name}.json"
    
    if os.path.exists(filepath):
        existing = read_tabungan(name)
        data["created_at"] = existing.get("created_at", now)
    else:
        data["created_at"] = now

    data["updated_at"] = now

    with open(filepath, "w") as f:
        json.dump(data, f)

def hitung_hari_sampai_lunas(data):
    if data["current"] < data["target"]:
        return "Belum lunas"
    
    try:
        created = datetime.strptime(data["created_at"], "%Y-%m-%d %H:%M:%S")
        updated = datetime.strptime(data["updated_at"], "%Y-%m-%d %H:%M:%S")
        selisih = (updated - created).days
        return f"{selisih} hari"
    except:
        return "-"

def input_int(prompt_text, default=0):
    try:
        return int(Prompt.ask(prompt_text))
    except ValueError:
        console.print("[red]Input harus berupa angka.[/red]")
        return default

def wait_for_enter():
    global stop_thread
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == '\n':  # Enter ditekan
                stop_thread = True
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def menu_create():
    console.clear()
    console.print(Panel.fit("[bold cyan]Buat Tabungan Baru[/bold cyan]"))
    name = Prompt.ask("Masukkan nama tabungan")
    target = input_int("Masukkan target nominal")
    write_tabungan(name, {"target": target, "current": 0})
    console.print("[green]Tabungan berhasil dibuat![/green]")

def show_progress(current, target):
    percent = min(int((current / target) * 100), 100) if target else 0
    bar = f"[{'█' * (percent // 10)}{' ' * (10 - percent // 10)}] {percent}%"
    return bar

def menu_list():
    console.clear()
    tabungan = list_tabungan()
    if not tabungan:
        console.print("[bold yellow]Belum ada tabungan.[/bold yellow]")
        return

    table = Table(title="📋 Daftar Tabungan")
    table.add_column("No", justify="right")
    table.add_column("Nama Tabungan")
    table.add_column("Terkumpul", justify="right")
    table.add_column("Target", justify="right")
    table.add_column("Status")
    table.add_column("Progress")
    table.add_column("Dibuat", justify="center")
    table.add_column("Terakhir Diubah", justify="center")
    table.add_column("Hari Sampai Lunas", justify="center")

    for i, name in enumerate(tabungan, 1):
        data = read_tabungan(name)
        created = data.get("created_at", "-")
        updated = data.get("updated_at", "-")
        hari_lunas = hitung_hari_sampai_lunas(data)
        current, target = data["current"], data["target"]
        status = "✅" if current >= target else "⏳"
        progress_bar = show_progress(current, target)
        table.add_row(str(i), name, f"Rp {current:,}", f"Rp {target:,}", status, progress_bar, created, updated, hari_lunas)

    console.print(table)

def menu_edit():
    tabungan = list_tabungan()
    if not tabungan:
        console.print("[bold red]Tidak ada tabungan untuk diedit.[/bold red]")
        return

    console.clear()
    console.print(Panel.fit("[bold cyan]Edit Tabungan[/bold cyan]"))
    for i, name in enumerate(tabungan, 1):
        console.print(f"[{i}] {name}")
    index = input_int("Pilih nomor tabungan") - 1

    if index < 0 or index >= len(tabungan):
        console.print("[red]Pilihan tidak valid.[/red]")
        return

    name = tabungan[index]
    data = read_tabungan(name)
    created = data.get("created_at", "-")
    updated = data.get("updated_at", "-")
    hari_lunas = hitung_hari_sampai_lunas(data)
    while True:
        os.system("clear")
        console.print(Panel.fit(f"[bold magenta]Edit: {name}[/bold magenta]\n"
                                f"Terkumpul: Rp {data['current']:,} / Rp {data['target']:,}\n"
                                f"Progress: {show_progress(data['current'], data['target'])}\n\n" f"[cyan]Hari sampai lunas:[/] {hari_lunas}\n\n" f"[cyan]Dibuat:[/] {created}\n" f"[cyan]Terakhir Diubah:[/] {updated}" ))
        console.print("1. Tambah Nominal")
        console.print("2. Kurangi Nominal")
        console.print("3. Ganti Nama")
        console.print("4. Ganti Target")
        console.print("5. Hapus Tabungan")
        console.print("6. Kembali")
        pilihan = Prompt.ask("Pilih menu", choices=["1", "2", "3", "4", "5", "6"])

        if pilihan == "1":
            os.system("clear")
            console.clear()
            amt = input_int("Jumlah yang ditabung")
            data["current"] += amt
            write_tabungan(name, data)
        elif pilihan == "2":
            os.system("clear")
            console.clear()
            amt = input_int("Jumlah pengeluaran")
            data["current"] = max(0, data["current"] - amt)
            write_tabungan(name, data)
        elif pilihan == "3":
            os.system("clear")
            console.clear()
            new_name = Prompt.ask("Nama baru")
            os.rename(f"{DATA_DIR}/{name}.json", f"{DATA_DIR}/{new_name}.json")
            write_tabungan(new_name, data)
            name = new_name
        elif pilihan == "4":
            os.system("clear")
            console.clear()
            new_target = input_int("Target baru")
            data["target"] = new_target
            write_tabungan(name, data)
        elif pilihan == "5":
            if Confirm.ask("Yakin ingin menghapus tabungan ini?"):
                os.remove(f"{DATA_DIR}/{name}.json")
                console.print("[red]Tabungan dihapus.[/red]")
                return
        elif pilihan == "6":
            console.clear()
            break

def menu_information():
    global stop_thread
    stop_thread = False
    console.clear()

    def generate_layout():
        nowJ = datetime.now().strftime("%H:%M:%S.%f")
        nowT = datetime.now().strftime("%Y-%m-%d")

        # Panel informasi umum
        content_general = (
            f"[bold]Tanggal:[/] {nowT}\n"
            f"[bold]Jam:[/] {nowJ}\n"
        )
        panel_general = Panel.fit(content_general, border_style="green", title="Time Information")

        # Panel informasi fungsi aplikasi
        content_info = (
            "- Aplikasi ini mencatat tabungan pribadi Anda secara lokal.\n"
            "- Anda bisa membuat, mengedit, melihat, dan menghapus tabungan.\n"
            "- Data disimpan di file teks secara otomatis.\n"
            "- Estimasi hari lunas dihitung saat target tercapai.\n"
        )
        panel_info = Panel.fit(content_info, border_style="cyan", title="App Information")
        
        #Panel informasi creator
        content_creator = (
            "[bold]Pemilik:[/] Putrazaubadillah\n"
            "[bold]Pembuat:[/] Putrazaubadillah\n"
            "[bold]Version:[/] V2.0.0\n\n\n"
            f"[#7f7f7f]{'Tanggal:'.center(35)}[/#7f7f7f]\n"
            f"[#7f7f7f]{'01-08-2025'.center(35)}[/#7f7f7f]\n"
          )
        panel_creator = Panel.fit(content_creator, border_style="purple", title="Creator Information")

        # Layout dua bagian atas & bawah
        layout = Layout()
        layout.split(
            Layout(Align.center(panel_general), name="atas", size=9),
            Layout(Align.center(panel_info), name="tengah"),
            Layout(Align.center(panel_creator), name="bawah2"),
            Layout(Align.center("[dim]Tekan Enter untuk kembali...[/dim]"), name="bawah_text", size=3),
        )
        return layout

    # Jalankan thread untuk deteksi Enter
    input_thread = threading.Thread(target=wait_for_enter, daemon=True)
    input_thread.start()

    # Jalankan tampilan dinamis sampai Enter ditekan
    with Live(generate_layout(), refresh_per_second=2, screen=True) as live:
        while not stop_thread:
            sleep(0.01)
            live.update(generate_layout())

def main_menu():
    while True:
        os.system("clear")
        console.clear()
        
        # Konten panel: gabungan judul dan menu
        panel_content = Text(justify="center")
        panel_content.append("💰 C E L E N G A N K U\n", style="bold green")
        panel_content.append("\n")
        panel_content.append("1.", style="bold cyan")
        panel_content.append(" Create Tabungan\n")
        panel_content.append("2.", style="bold cyan")
        panel_content.append(" Edit Tabungan\n")
        panel_content.append("3.", style="bold cyan")
        panel_content.append(" List Tabungan\n")
        panel_content.append("4.", style="bold cyan")
        panel_content.append(" Information\n")
        panel_content.append("5.", style="bold cyan")
        panel_content.append(" Exit")

        # Buat panel yang akan ditaruh di tengah layar
        menu_panel = Panel(
            panel_content,
            title="Menu Utama",
            border_style="bright_blue",
            box=ROUNDED,
            padding=(1, 4),
        )

        # Tampilkan panel di tengah layar
        console.print(Align.center(menu_panel, vertical="middle"))

        # Input pilihan di bawah panel, tapi tetap rata tengah# Tampilkan teks di tengah dulu
        judul = Align.center("[bold cyan]💰 Aplikasi Celenganku 💰[/bold cyan]")
        menu = Align.center("[bold]Pilih menu[/bold]")
        
        console.print(judul)
        console.print(menu)
        
        # Baru panggil Prompt.ask biasa (tanpa Align)
        pilihan = Prompt.ask(">>>", choices=["1", "2", "3", "4", "5"])


        if pilihan == "1":
            menu_create()
        elif pilihan == "2":
            menu_edit()
        elif pilihan == "3":
            menu_list()
            console.input("[#7f7f7f]Tekan Enter untuk kembali ke menu utama...[/#7f7f7f]")
        elif pilihan == "4":
          menu_information()
        elif pilihan == "5":
            console.print("\n[bold yellow]Terima kasih! Sampai jumpa![/bold yellow]")
            break
          

if __name__ == "__main__":
    main_menu()
