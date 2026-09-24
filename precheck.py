import ssl
import socket
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl

def verify_dns_resolution(hostname):
    """Verifies if the current container/pod environment can resolve the target FQDN."""
    try:
        ip_address = socket.gethostbyname(hostname)
        print(f"  ✅ DNS: Successfully resolved '{hostname}' to {ip_address}.")
        return True
    except socket.gaierror as e:
        print(f"  ❌ DNS: Failed to resolve host '{hostname}'. Ensure your Kubernetes CoreDNS Upstream Forwarders include your vSphere DNS servers. Error: {str(e)}")
        return False

def verify_tcp_port(ip_or_host, port, timeout=3):
    """Performs a brief socket handshake to confirm network line-of-sight."""
    try:
        with socket.create_connection((ip_or_host, port), timeout=timeout):
            print(f"  ✅ Network: TCP port {port} is open on {ip_or_host}.")
            return True
    except (socket.timeout, ConnectionRefusedError, socket.gaierror) as e:
        print(f"  ❌ Network: Failed to connect to {ip_or_host}:{port}. Details: {str(e)}")
        return False

def run_vm_migration_prechecks(vm_name, host, user, password, required_privileges):
    passed = True

    # ==========================================
    # CHECK 1: Pod CoreDNS Resolution for vCenter
    # ==========================================
    print(f"=== 1. Validating vCenter DNS & Connectivity ===")
    if not verify_dns_resolution(host):
        passed = False
        print("❌ FAIL: vCenter hostname unresolvable from this pod. Aborting further checks.")
        return
        
    #if not verify_tcp_port(host, 443):
    #    passed = False
    #    print("❌ FAIL: Cannot reach vCenter on management port 443. Aborting inventory checks.")
    #    return

    # ==========================================
    # CHECK 2: vCenter Authentication
    # ==========================================
    try:
        context = ssl._create_unverified_context()
        si = SmartConnect(host=host, user=user, pwd=password, port = "8989", sslContext=context)
        content = si.RetrieveContent()
        print("✅ PASS: Successfully authenticated with vCenter Server.")
    except vmodl.MethodFault as e:
        print(f"❌ FAIL: Authentication failed. Details: {e.msg}")
        return
    except Exception as e:
        print(f"❌ FAIL: pyVmomi layer crash connecting to vCenter. Details: {str(e)}")
        return

    try:
        # Locate the VM via Container View
        container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        target_vm = None
        for vm in container.view:
            if vm.name == vm_name:
                target_vm = vm
                break
                
        if not target_vm:
            print(f"❌ Error: VM '{vm_name}' not found.")
            Disconnect(si)
            return

        print(f"\n=== Running Kubernetes Migration Prechecks for: {target_vm.name} ===")

        # ==========================================
        # CHECK 3: Dynamic ESXi Host DNS & Port 902
        # ==========================================
        print(f"\n--- Data Plane Verification ---")
        esxi_host_obj = target_vm.runtime.host
        if esxi_host_obj:
            esxi_name = esxi_host_obj.name
            print(f"ℹ️  Target VM resides on ESXi Host: '{esxi_name}'")
            
            # Step A: Validate Pod can resolve the ESXi Host FQDN registered in vCenter
            if not verify_dns_resolution(esxi_name):
                print(f"❌ FAIL: The migration pod cannot resolve the ESXi host FQDN '{esxi_name}'. Migration streaming will fail.")
                passed = False
            
            # Step B: Validate Port 902 access for raw disk streaming (VDDK/NBD)
            if not verify_tcp_port(esxi_name, 902):
                print(f"❌ FAIL: Port 902 blocked on ESXi host '{esxi_name}'. Migration stream blocked.")
                passed = False
            else:
                print(f"✅ PASS: Data plane connectivity confirmed for host '{esxi_name}'.")
        else:
            print("❌ FAIL: Unable to resolve parent ESXi host for runtime state calculation.")
            passed = False

        # ==========================================
        # CHECK 4: Permissions / Privileges Check
        # ==========================================
        print(f"\n--- Authorization Verification ---")
        auth_manager = content.authorizationManager
        vc_permissions = auth_manager.FetchUserPrivilegeOnEntities(entities=[target_vm], userName=user)

        #for result in vc_permissions:
        #    # Access the privilege attribute on each individual item
        #    print(f"Entity: {result.entity}, Privileges: {result.privileges}")

        user_privileges = vc_permissions[0].privileges if vc_permissions else []
       
        missing_privileges = [priv for priv in required_privileges if priv not in user_privileges]
        if missing_privileges:
            print(f"❌ FAIL: Missing required vSphere privileges on this VM: {', '.join(missing_privileges)}")
            passed = False
        else:
            print("✅ PASS: User possesses all required vSphere migration privileges.")

        # ==========================================
        # CHECK 5: Hardware & Blueprint Configuration
        # ==========================================
        print(f"\n--- Artifact & Compatibility Verification ---")

        snapshot_info = getattr(target_vm, 'snapshot', None)

        if snapshot_info is not None:
            # The VM has snapshots
            snapshots = snapshot_info.rootSnapshotList
            print(f"Found {len(snapshots)} root snapshot(s).")
            print("❌ FAIL: VM has active snapshots. Consolidate snapshots before migrating.")
            passed = False
        else:
            print("✅ PASS: No active snapshots found.")


        has_attached_iso = False
        has_rdm = False
        
        for device in target_vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualCdrom):
                if hasattr(device.backing, 'fileName') and device.backing.fileName:
                    print(f"❌ FAIL: Mounted ISO found on CD-ROM: {device.backing.fileName}")
                    has_attached_iso = True
                    passed = False
                    
            if isinstance(device, vim.vm.device.VirtualDisk):
                backing = device.backing
                if isinstance(backing, vim.vm.device.VirtualDisk.RawDiskMappingVer1BackingInfo):
                    print(f"❌ FAIL: Raw Device Mapping (RDM) disk found: {device.deviceInfo.label}")
                    has_rdm = True
                    passed = False

        if not has_attached_iso:
            print("✅ PASS: No mounted ISO files detected.")
        if not has_rdm:
            print("✅ PASS: No Raw Device Mappings (RDM) detected.")

        # Summary Spec Metadata
        cpus = target_vm.config.hardware.numCPU
        memory_mb = target_vm.config.hardware.memoryMB
        print(f"ℹ️  SPEC METADATA -> vCPUs: {cpus}, RAM: {memory_mb}MB")

        print("\n====================================================")
        if passed:
            print("🎉 STATUS: Ready for Migration Blueprinting!")
        else:
            print("⚠️  STATUS: Fix flagged configuration, DNS, or network blockages.")
            
    finally:
        Disconnect(si)

if __name__ == "__main__":
    required_privileges = ["VirtualMachine.Config.Resource"]
    run_vm_migration_prechecks("tkg-cluster-01-md-0-f6b67bf8b-l459w", "172.17.0.66", "user", "pass", required_privileges)

