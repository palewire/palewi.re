script "Add New Relic package source" do
  interpreter "bash"
  user "root"
  group "root"
  code <<-EOH
    echo deb http://apt.newrelic.com/debian/ newrelic non-free >> /etc/apt/sources.list.d/newrelic.list
  EOH
end

script "Trust New Relic GPG key" do
  interpreter "bash"
  user "root"
  group "root"
  code <<-EOH
    wget -O- https://download.newrelic.com/548C16BF.gpg | apt-key add -
  EOH
end

script "Update package list" do
  interpreter "bash"
  user "root"
  group "root"
  code <<-EOH
    apt-get update
  EOH
end

script "Install service monitor package" do
  interpreter "bash"
  user "root"
  group "root"
  code <<-EOH
    apt-get install newrelic-sysmond
  EOH
end

script "Configure server monitor" do
  interpreter "bash"
  user "root"
  group "root"
  code <<-EOH
    nrsysmond-config --set license_key=#{node['newrelic_license_key']}
  EOH
end

script "Start server monitor" do
  interpreter "bash"
  user "root"
  group "root"
  code <<-EOH
    /etc/init.d/newrelic-sysmond start
  EOH
end

script "Install Python agent" do
  interpreter "bash"
  user "root"
  group "root"
  code <<-EOH
    pip install newrelic
  EOH
end

script "Install Python configuration" do
  interpreter "bash"
  user "root"
  group "root"
  code <<-EOH
    pip install newrelic
  EOH
end

script "restart-apache" do
  interpreter "bash"
  user "root"
  code <<-EOH
    apachectl restart
  EOH
end