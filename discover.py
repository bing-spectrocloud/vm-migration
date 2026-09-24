# pip install pyvmomi
# run from home directory

import ssl
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect


def main():


    # Define connection details matching your running vcsim instance
    # curl -k  https://user:pass@172.17.0.66:8989/about

    try:

        # Create an unverified SSL context
        
        context = ssl._create_unverified_context()
        #context = ssl.create_default_context()
        #context.check_hostname = False
        #context.verify_mode = ssl.CERT_NONE

        # Connect using the sslContext parameter
        si = SmartConnect(
            host = "172.17.0.66",
            user = "user",
            pwd = "pass",
            port = "8989",
            sslContext=context
        )

        # Retrieve the ServiceContent and target the root folder
        content = si.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder,
            [vim.Datacenter, vim.HostSystem, vim.VirtualMachine],
            True
        )

        print("\n--- Simulated Inventory Found ---")
        for obj in container.view:
            if isinstance(obj, vim.Datacenter):
                print(f"🏢 Datacenter: {obj.name}")
            elif isinstance(obj, vim.HostSystem):
                print(f"🖥️  ESXi Host:  {obj.name}")
            elif isinstance(obj, vim.VirtualMachine):
                print(f"⚡ VM:         {obj.name}")

        # Disconnect gracefully when done
        Disconnect(si)
        print("\nDisconnected successfully.")

    except Exception as e:
        print(f"Failed to connect to vcsim: {e}")

if __name__ == "__main__":
    main()


