# Load any base system wide packages
node[:base_packages].each do |pkg|
    package pkg do
        :upgrade
    end
end

# Loop through the user list, create the user, load the authorized_keys
# and mint a bash_profile
node[:users].each_pair do |username, info|
    group username do
       gid info[:id] 
    end

    user username do 
        comment info[:full_name]
        uid info[:id]
        gid info[:id]
        shell info[:disabled] ? "/sbin/nologin" : "/bin/bash"
        supports :manage_home => true
        home "/home/#{username}"
    end

    directory "/home/#{username}/.ssh" do
        owner username
        group username
        mode 0700
    end

    cookbook_file "/home/#{username}/.ssh/authorized_keys" do
      source "authorized_keys"
      mode 0640
      owner "palewire"
      group "palewire"
    end

    cookbook_file "/home/#{username}/.bash_profile" do
        source "bash_profile"
        owner username
        group username
        mode 0755
    end

end

# Set the user groups
node[:groups].each_pair do |name, info|
    group name do
        gid info[:gid]
        members info[:members]
    end
end

# Load the authorized keys for the root user
directory "/root/.ssh" do
    owner "root"
    group "root"
    mode 0700
end

cookbook_file "/root/.ssh/authorized_keys" do
  source "authorized_keys"
  mode 0640
  owner "root"
  group "root"
end


