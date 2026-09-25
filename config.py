
host =  "172.17.0.66"
user = "user"
passwd = "pass"

vm= "tkg-cluster-01-md-0-f6b67bf8b-l459w"

required_privileges = [
  "Datastore.Browse",
  "Datastore.FileManagement",
  "Global.CancelTask",
  "Network.Assign",
  "Resource.AssignVMToPool",
  "System.Anonymous",
  "System.Read",
  "System.View",
  "VirtualMachine.Config.AdvancedConfig",
  "VirtualMachine.Config.Settings",
  "VirtualMachine.Interact.PowerOff",
  "VirtualMachine.Inventory.CreateFromExisting",
  "VirtualMachine.Provisioning.DiskAccess",
  "VirtualMachine.Provisioning.DiskManagement",
  "VirtualMachine.Provisioning.Export",
  "VirtualMachine.State.CreateSnapshot",
  "VirtualMachine.State.RemoveSnapshot"
    ]

#https://libguestfs.org/virt-v2v-support.1.html
virt_v2v_supported_guest_os = {
    # Red Hat / CentOS / Rocky / Alma Linux
    'rhel4Guest', 'rhel4_64Guest', 'rhel5Guest', 'rhel5_64Guest',
    'rhel6Guest', 'rhel6_64Guest', 'rhel7Guest', 'rhel7_64Guest',
    'rhel8_64Guest', 'rhel9_64Guest', 'centosGuest', 'centos64Guest',
    'centos7Guest', 'centos7_64Guest', 'centos8_64Guest', 'centos9_64Guest',
    # Ubuntu / Debian
    'ubuntuGuest', 'ubuntu64Guest', 'debian4Guest', 'debian4_64Guest',
    'debian5Guest', 'debian5_64Guest', 'debian6Guest', 'debian6_64Guest',
    'debian7Guest', 'debian7_64Guest', 'debian8Guest', 'debian8_64Guest',
    'debian9Guest', 'debian9_64Guest', 'debian10Guest', 'debian10_64Guest',
    'debian11_64Guest', 'debian12_64Guest',
    # Windows Server & Desktop
    'windows7Guest', 'windows7_64Guest', 'windows8Guest', 'windows8_64Guest',
    'windows9Guest', 'windows9_64Guest', 'windows10Guest', 'windows10_64Guest',
    'windows11_64Guest', 'windows7Server64Guest', 'windows8Server64Guest',
    'longhornGuest', 'longhorn64Guest', 'winNetBusinessGuest', # Server 2008 / 2012 / 2016 / 2019 / 2022 / 2025
}

check_dns = False
check_443 = False
check_vm = True
check_902  = False  # for VDDK 
