import argparse
import random
import time
import pyfiglet
import requests
import sys
from termcolor import colored
import urllib3
import statistics

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS_TECHNOLOGIES = {
    "x-proxy-cache":"Unknown",
    "age":"Unknown",
    "cf-cache-status": "Cloudflare",
    "x-cache": "Akamai, CloudFront (AWS), Fastly, Varnish",
    "x-cache-hits": "Fastly",
    "akamai-cache-status": "Akamai",
}

def check_headers(url, log_file, HEADERS_TO_CHECK, threshold, hit_requests):
    try:
        timings = []

        # First request (baseline)
        start = time.time()
        response1 = requests.get(url, timeout=10, allow_redirects=True, verify=False)
        t1 = time.time() - start
        timings.append(t1)

        # Additional requests (possible hits)
        for _ in range(hit_requests):
            start = time.time()
            response2 = requests.get(url, timeout=10, allow_redirects=True, verify=False)
            timings.append(time.time() - start)

        median_hit_time = statistics.median(timings[1:])
        baseline_time = timings[0]

        if median_hit_time <= threshold * baseline_time:
            headers = response2.headers
            cache_header_found = False

            for header, value in response2.headers.items():

                if header.lower() in HEADERS_TO_CHECK:
                    print(f"{url} (H: {median_hit_time:.2f}s, M: {baseline_time:.2f}s) -> {header}: {value}"+colored(f" ({HEADERS_TECHNOLOGIES.get(header.lower(), 'Unknown')})", "green"))
                    log_file.write(f"{url} (H: {median_hit_time:.2f}s, M: {baseline_time:.2f}s) -> {header}: {value} ({HEADERS_TECHNOLOGIES.get(header.lower(), 'Unknown')})\n")
                    cache_header_found = True
                    break

            if not cache_header_found:
                print(f"{url} (H: {median_hit_time:.2f}s, M: {baseline_time:.2f}s) -> {colored("No cache-related headers found.", "yellow")}")
                log_file.write(f"{url} (H: {median_hit_time:.2f}s, M: {baseline_time:.2f}s) -> No cache-related headers found.\n")

        else:
            print(f"{url} -> No cache detected (H: {median_hit_time:.2f}s, M: {baseline_time:.2f}s)")

    except requests.RequestException as e:
        print(f"{url} -> " + colored("Error", "red") + f" ({e})")

def print_banner(args, total_urls):
    banner_text = pyfiglet.figlet_format("CacHeIT", font="slant")
    print(colored(banner_text, "cyan"))

    # Print parameter recap
    print(colored("Starting cache detection scan with the following parameters:", "yellow"))
    print(f"  Input file       : {args.i}")
    print(f"  Output file      : {args.o}")
    print(f"  Threshold ratio  : {args.t}")
    print(f"  Hit requests (-r): {args.hits}")

    print(f"  Total URLs       : {total_urls}")

    print(colored("="*60, "yellow"))

def main():
    parser = argparse.ArgumentParser(description="Cache detection script")
    parser.add_argument("-t", type=float, default=0.5,
                        help="Hit/Miss time ratio threshold (default: 0.5)")
    parser.add_argument("-i", type=str, default="input.txt",
                        help="Input file containing URLs (default: input.txt)")
    parser.add_argument("-o", type=str, default="cache_detection_results.txt",
                        help="Output log file (default: cache_detection_results.txt)")
    parser.add_argument("-r", "--hits", type=int, default=2,
                        help="HTTP requests after the first to detect HITs (default: 2)")

    args = parser.parse_args()

    HEADERS_TO_CHECK = list(HEADERS_TECHNOLOGIES.keys())

    try:
        url = ''

        with open(args.i, "r") as f:
            urls = [line.strip() for line in f if line.strip()]

        total_urls = len(urls)
        print_banner(args, total_urls)

        # Open output file once
        with open(args.o, "a") as log_file:
            for line in urls:
                r = random.randint(1000000, 9999999)

                if line.endswith("/"):
                    url = line + "?cbuster=" + str(r)
                else:
                    url = line + "/?cbuster=" + str(r)

                check_headers(url, log_file, HEADERS_TO_CHECK, args.t, hit_requests=int(args.hits))

    except FileNotFoundError:
        print(colored(f"Input file not found: {args.i}", "red"))
        sys.exit(1)


if __name__ == "__main__":
    main()
