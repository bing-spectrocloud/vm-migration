import config
import ssl
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect


def main():


    # Define connection details matching your running vcsim instance
    # curl -k  https://user:pass@172.17.0.66:8989/about

    try:

        # Create an unverified SSL context
        # Connect using sslContext parameter
        context = ssl._create_unverified_context()
        si = SmartConnect(host=config.host, user=config.user, pwd=config.passwd, port = "8989", sslContext=context)

        # Retrieve the ServiceContent and target the root folder
        content = si.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder,
            [vim.Datacenter, vim.HostSystem, vim.VirtualMachine, vim.Network, vim.Datastore],
            True
        )

        print("\n--- Simulated Inventory Found ---")
        for obj in container.view:
            if isinstance(obj, vim.Datacenter):
                print(f"🏢 Datacenter: {obj.name}")
                print("-" * 40)
            elif isinstance(obj, vim.Datastore):
                print(f"🏢 DataStore: {obj.name}")
                datastore= obj
                summary = datastore.summary

                # Convert capacities from bytes to Gigabytes
                capacity_gb = round(summary.capacity / (1024**3), 2)
                free_gb = round(summary.freeSpace / (1024**3), 2)
    
                print(f" {summary.type:<8} Capacity(GB): {capacity_gb:<15}, Free(GB): {free_gb:<15} {str(summary.accessible):<10}")

                print("-" * 40)
            elif isinstance(obj, vim.HostSystem):
                print(f"🖥️  ESXi Host:  {obj.name}")
                host= obj
                print(f"  Connection State: {host.summary.runtime.connectionState}")
                print(f"  Power State: {host.summary.runtime.powerState}")
                print(f"  Model: {host.summary.hardware.model}")
                print(f"  CPU Mhz: {host.summary.hardware.cpuMhz}")
                print(f"  Num CPU Cores: {host.summary.hardware.numCpuCores}")
                print(f"  Memory (GB): {host.summary.hardware.memorySize / (1024**3):.2f}")
                print(f"  Host OS: {host.summary.config.product.fullName:<50}")
                print("-" * 40)
            elif isinstance(obj, vim.VirtualMachine):
                print(f"⚡ VM:         {obj.name}")
                vm= obj

                # Extract Configured and Actual Guest OS IDs
                config_guest_id = vm.summary.config.guestId             # What is in the .vmx file
                config_guest_name = vm.summary.config.guestFullName

                runtime_guest_id = None
                runtime_guest_name = None

                # Runtime info is only available if the VM is powered on with VMware Tools installed
                if vm.summary.guest is not None:
                    runtime_guest_id = vm.summary.guest.guestId
                    runtime_guest_name = vm.summary.guest.guestFullName

                print(f"  OS Check")
                print(f"    Configured OS ID:   {config_guest_id} ({config_guest_name})")
                print(f"    Runtime OS ID:      {runtime_guest_id} ({runtime_guest_name})")


                boot_options = vm.config.bootOptions
                print(f"  Boot Options")
                print(f"    Boot Delay (ms): {boot_options.bootDelay}")
                print(f"    Enter BIOS/UEFI Setup on next boot: {boot_options.enterBIOSSetup}")
                print(f"    Firmware type (bios or efi): {vm.config.firmware}")
                print("-" * 40)
            elif isinstance(obj, vim.Network):
                print(f" 🖧 Network: {obj.name}")
                net=obj
                print(f"  Type: {type(net).__name__}")
                if hasattr(net, 'summary'):
                    print(f"  Accessible: {net.summary.accessible}")
                    print(f"  Datacenter: {net.summary.name}")
                    print("-" * 40)

        # Disconnect gracefully when done
        Disconnect(si)
        print("\nDisconnected successfully.")

    except Exception as e:
        print(f"Failed to connect to vcsim: {e}")

if __name__ == "__main__":
    main()


