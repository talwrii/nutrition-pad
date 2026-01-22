#!/usr/bin/env python3
"""
Watchdog script to monitor nutrition-pad server health and restart if needed.

This script monitors the /heartbeat endpoint to ensure the tablet client
is still responding. If no heartbeat is received for a configurable timeout
period, the server process is restarted.
"""
import time
import sys
import os
import signal
import argparse
import requests
from datetime import datetime

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def check_heartbeat(url, timeout):
    """
    Check if heartbeat is recent enough.

    Args:
        url: Full URL to the heartbeat endpoint
        timeout: Maximum seconds since last heartbeat

    Returns:
        tuple: (is_alive, last_heartbeat_age_seconds)
    """
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            last_heartbeat = data.get('timestamp')
            if last_heartbeat:
                age = time.time() - last_heartbeat
                return (age < timeout, age)
        return (False, None)
    except Exception as e:
        log(f"Error checking heartbeat: {e}")
        return (False, None)

def get_server_pid(pidfile):
    """Read PID from pidfile"""
    try:
        with open(pidfile, 'r') as f:
            return int(f.read().strip())
    except Exception as e:
        log(f"Error reading PID file: {e}")
        return None

def kill_server(pid):
    """Kill the server process"""
    try:
        os.kill(pid, signal.SIGTERM)
        log(f"Sent SIGTERM to process {pid}")
        # Wait for graceful shutdown
        time.sleep(5)
        # Check if still alive
        try:
            os.kill(pid, 0)
            # Still alive, force kill
            os.kill(pid, signal.SIGKILL)
            log(f"Sent SIGKILL to process {pid}")
        except OSError:
            # Process is dead
            pass
        return True
    except Exception as e:
        log(f"Error killing process: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Watchdog for nutrition-pad server")
    parser.add_argument('--url', default='http://localhost:5001/heartbeat',
                       help='Heartbeat endpoint URL')
    parser.add_argument('--timeout', type=int, default=60,
                       help='Heartbeat timeout in seconds (default: 60)')
    parser.add_argument('--check-interval', type=int, default=15,
                       help='How often to check heartbeat in seconds (default: 15)')
    parser.add_argument('--pidfile', default='/tmp/nutrition-pad.pid',
                       help='PID file for the server process')
    parser.add_argument('--restart-command',
                       help='Command to restart server (if not provided, only kills)')
    args = parser.parse_args()

    log("Watchdog started")
    log(f"Monitoring: {args.url}")
    log(f"Timeout: {args.timeout}s")
    log(f"Check interval: {args.check_interval}s")

    consecutive_failures = 0
    max_consecutive_failures = 3

    while True:
        try:
            is_alive, age = check_heartbeat(args.url, args.timeout)

            if is_alive:
                if age is not None:
                    log(f"Heartbeat OK (age: {age:.1f}s)")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if age is not None:
                    log(f"WARNING: Heartbeat stale (age: {age:.1f}s) - failure {consecutive_failures}/{max_consecutive_failures}")
                else:
                    log(f"WARNING: Cannot reach heartbeat endpoint - failure {consecutive_failures}/{max_consecutive_failures}")

                if consecutive_failures >= max_consecutive_failures:
                    log("CRITICAL: Maximum consecutive failures reached")

                    # Try to kill the server
                    pid = get_server_pid(args.pidfile)
                    if pid:
                        log(f"Killing server process {pid}")
                        if kill_server(pid):
                            log("Server killed successfully")

                            # Restart if command provided
                            if args.restart_command:
                                log(f"Restarting server: {args.restart_command}")
                                os.system(args.restart_command)
                                time.sleep(10)  # Wait for server to start
                            else:
                                log("No restart command provided - exiting")
                                sys.exit(1)
                        else:
                            log("Failed to kill server")
                    else:
                        log("Cannot find server PID - unable to restart")
                        if args.restart_command:
                            log(f"Attempting to start server: {args.restart_command}")
                            os.system(args.restart_command)
                            time.sleep(10)

                    consecutive_failures = 0

            time.sleep(args.check_interval)

        except KeyboardInterrupt:
            log("Watchdog stopped by user")
            sys.exit(0)
        except Exception as e:
            log(f"Unexpected error: {e}")
            time.sleep(args.check_interval)

if __name__ == '__main__':
    main()
