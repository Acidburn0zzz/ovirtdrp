#!/bin/env python
from __future__ import print_function
from getpass import getpass
from functions_ovirt import *


def main():
    config = read_config(file_config='/etc/ovirtdrp/config.yml')
    manager = config['manager']
    url_manager = 'https://' + manager
    hosts = config["Hosts"]

    database = decrypt(config['database'])
    db_user = decrypt(config['userDatabase'])
    db_password = decrypt(config['passDatabase'])
    iscsi_luns = config['luns']
    iscsi_portals = config['mpath']

    if ping(manager):
        print("Please enter username for %s" % manager)
        username = raw_input("Username: ")
        if not username:
            print("Username must not be empty")
            sys.exit(-3)
        else:
            print("Please enter password for %s (will not be echoed)" % manager)
            password = getpass()
            if not password:
                print("Password must not be empty")
                sys.exit(-3)
        api = connect(manager_url=url_manager, manager_password=password, manager_username=username)
    else:
        print("%s is unreacheable" % manager)
        sys.exit(4)

    while True:
        clear()
        menu()
        option = raw_input("Choice: ")

        if option == "2":
            break
        elif option == "1":
            hosts['local'] = (get_local_hosts(api=api, remote=hosts['remote']))
            if status(api=api, hosts=hosts):
                sub_menu()
                sub_option = raw_input("Choice: ")
                if sub_option == "2":
                    break
                elif sub_option == "1":
                    print("Initializing DRP")
                    for host in hosts['local']:
                        if ((status_one_host(api, host)) == 'non_responsive') \
                                or ((status_one_host(api, host)) == 'down'):
                            print("Fencing host {}".format(host))
                            if do_fence_host(api, host):
                                print("Fencing host {} OK".format(host))
                                print("Set Maintenance host {}".format(host))
                                if do_maintenance_host(api, host):
                                    print("Maintenance host {} OK".format(host))
                                else:
                                    print("Error trying to set Maintenance")
                            else:
                                print("Error trying to set Fencing")
                        elif (status_one_host(api, host)) == 'maintenance':
                            print("Maintenance host %s OK" % host)
                    print("Updating storage connections")
                    update_connections(db_user=db_user,
                                       db_password=db_password, database=database,
                                       manager=manager, lunsArray=iscsi_luns, portalsArray=iscsi_portals)
                    for host in hosts['remote']:
                        if do_activate_host(api, host):
                            print("Activating %s OK" % host)
                        else:
                            print("Failed to activate %s" % host)
                    drp_finish(api)
            else:
                print("Not Continue")
                sys.exit(5)
            raw_input("Press Enter to Exit...")
            sys.exit(1)
        else:
            print("{} is not a valid option".format(option))
            raw_input("Press Enter to continue...")


if __name__ == '__main__':
    main()
