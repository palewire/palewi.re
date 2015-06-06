# Install apache
package "apache2" do
    :upgrade
end

# Install mod-wsgi so apache can talk to Django
package "libapache2-mod-wsgi" do
    :upgrade
end

# install mod-rpaf so apache can use the X-Forwarded-For
# header to see the real incoming IP addresses. This prevents server-status
# from being publicly available
package "libapache2-mod-rpaf" do
    :upgrade
end

# Set the port for Apache since Varnish will be on :80
template "/etc/apache2/ports.conf" do
  source "apache/ports.conf.erb"
  mode 0640
  owner "root"
  group "root"
  variables({
     :apache_port => node[:apache_port]
  })
end

# Set a virtual host file for each app
node[:apps].each do |app|
    template "/etc/apache2/sites-enabled/#{app[:name]}" do
      source "apache/vhost.erb"
      mode 0640
      owner "root"
      group "root"
      variables({
         :apache_port => node[:apache_port],
         :server_name => app[:apache_server_name],
         :app_name => app[:name],
         :apps_user => node[:apps_user]
      })
    end
end

cookbook_file "/etc/apache2/apache2.conf" do
  source "apache/apache2.conf"
  mode 0640
  owner "root"
  group "root"
end

bash "Remove default apache config" do
  user "root"
  group "root"
  code "rm /etc/apache2/sites-enabled/000-default.conf"
  ignore_failure true
end

script "restart-apache" do
  interpreter "bash"
  user "root"
  code <<-EOH
    apachectl restart
  EOH
end