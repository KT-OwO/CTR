import subprocess
import time
import json
import os
import re

class SecurityScanner:
    def __init__(self, image_name, ddos_tool_path):
        self.image_name = image_name
        self.ddos_tool_path = ddos_tool_path
        self.container_id = None
        self.score = 100
        self.report = []

    def run_container(self):
        print(f"INFO: Running container from image: {self.image_name}")
        try:
            result = subprocess.run(["podman", "run", "-d", "-p", "5000:5000", self.image_name], capture_output=True, text=True, check=True)
            self.container_id = result.stdout.strip()
            print(f"INFO: Container {self.container_id[:12]} started.")
            time.sleep(5) # Wait for the app to start
            return True
        except FileNotFoundError:
            print("ERROR: `podman` command not found. Is Podman installed and in your PATH?")
            return False
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Error running container: {e.stderr}")
            return False

    def stop_container(self):
        if self.container_id:
            print(f"INFO: Stopping container {self.container_id[:12]}")
            try:
                subprocess.run(["podman", "stop", self.container_id], capture_output=True, text=True, check=True)
                subprocess.run(["podman", "rm", self.container_id], capture_output=True, text=True, check=True)
                print("INFO: Container stopped and removed.")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"WARN: Could not stop or remove container: {e}")

    def scan_vulnerabilities_with_trivy(self):
        print("INFO: Scanning image for vulnerabilities with Trivy...")
        try:
            result = subprocess.run(["trivy", "image", "--format", "json", self.image_name], capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            if data.get("Results"):
                for res in data["Results"]:
                    if "Vulnerabilities" in res:
                        for vuln in res["Vulnerabilities"]:
                            severity = vuln["Severity"]
                            vuln_id = vuln["VulnerabilityID"]
                            pkg_name = vuln["PkgName"]
                            points = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 2}.get(severity, 0)
                            self.score -= points
                            self.report.append(f"[-] ({severity}) {vuln_id} in {pkg_name} (-{points} points)")
            print("INFO: Trivy scan complete.")
        except FileNotFoundError:
            print("ERROR: `trivy` command not found. Please install Trivy.")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Trivy scan failed: {e.stderr}")
        except json.JSONDecodeError:
            print("ERROR: Failed to parse Trivy output.")

    def check_container_configuration(self):
        if not self.container_id:
            return
        print("INFO: Checking container configuration...")
        try:
            result = subprocess.run(["podman", "inspect", self.container_id], capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            user = data[0].get("Config", {}).get("User", "root")
            if user == "" or user == "0" or user == "root":
                self.score -= 20
                self.report.append("[-] Container is running as root user (-20 points)")
            print("INFO: Configuration check complete.")
        except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError, IndexError) as e:
            print(f"ERROR: Failed to inspect container: {e}")

    def run_ddos_simulation(self):
        if not self.container_id:
            return
        print("INFO: Running DDoS simulation...")
        try:
            target_url = "http://localhost:5000/"
            result = subprocess.run([self.ddos_tool_path, "-url", target_url, "-n", "100", "-c", "10"], capture_output=True, text=True)
            
            print("--- DDoS Tool stdout ---")
            print(result.stdout)
            if result.stderr:
                print("--- DDoS Tool stderr (Error Details) ---")
                print(result.stderr)

            total_match = re.search(r"Total Requests: (\d+)", result.stdout)
            success_match = re.search(r"Successful Requests: (\d+)", result.stdout)

            if total_match and success_match:
                total = int(total_match.group(1))
                success = int(success_match.group(1))
                if total > 0:
                    success_rate = (success / total) * 100
                    if success_rate < 100:
                        points = (100 - success_rate) * 0.5
                        self.score -= points
                        self.report.append(f"[-] DDoS resilience is low. {100-success_rate:.2f}% of requests failed. (-{points:.1f} points)")
            print("INFO: DDoS simulation complete.")
        except FileNotFoundError:
            print(f"ERROR: DDoS tool not found at '{self.ddos_tool_path}'. Please check the path.")
        except Exception as e:
            print(f"ERROR: An unexpected error occurred during DDoS simulation: {e}")

    def run_scans(self):
        self.scan_vulnerabilities_with_trivy()
        if self.run_container():
            self.check_container_configuration()
            self.run_ddos_simulation()
            self.stop_container()

    def print_report(self):
        print("\n--- Security Report ---")
        for line in self.report:
            print(line)
        print("\n-----------------------")
        print(f"Final Score: {max(0, self.score)} / 100")
        print("-----------------------")

if __name__ == "__main__":
    ddos_tool_executable_path = os.path.join("..", "ddos_tool", "ddos_tool.exe")
    scanner = SecurityScanner("localhost/vulnerable-app", ddos_tool_executable_path)
    scanner.run_scans()
    scanner.print_report()