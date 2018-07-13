# -*- encoding: utf-8 -*-
# stub: docker-sync 0.5.7 ruby lib

Gem::Specification.new do |s|
  s.name = "docker-sync".freeze
  s.version = "0.5.7"

  s.required_rubygems_version = Gem::Requirement.new(">= 0".freeze) if s.respond_to? :required_rubygems_version=
  s.require_paths = ["lib".freeze]
  s.authors = ["Eugen Mayer".freeze]
  s.date = "2018-03-28"
  s.description = "Sync your code live to docker-containers without losing any performance on OSX".freeze
  s.email = "eugen.mayer@kontextwork.de".freeze
  s.executables = ["docker-sync".freeze, "docker-sync-stack".freeze, "docker-sync-daemon".freeze]
  s.files = ["bin/docker-sync".freeze, "bin/docker-sync-daemon".freeze, "bin/docker-sync-stack".freeze]
  s.homepage = "https://github.com/EugenMayer/docker_sync".freeze
  s.licenses = ["GPL-3.0".freeze]
  s.required_ruby_version = Gem::Requirement.new(">= 2.0".freeze)
  s.rubygems_version = "2.5.2".freeze
  s.summary = "Docker Sync - Fast and efficient way to sync code to docker-containers".freeze

  s.installed_by_version = "2.5.2" if s.respond_to? :installed_by_version

  if s.respond_to? :specification_version then
    s.specification_version = 4

    if Gem::Version.new(Gem::VERSION) >= Gem::Version.new('1.2.0') then
      s.add_runtime_dependency(%q<thor>.freeze, [">= 0.20.0", "~> 0.20"])
      s.add_runtime_dependency(%q<gem_update_checker>.freeze, [">= 0.2.0", "~> 0.2.0"])
      s.add_runtime_dependency(%q<docker-compose>.freeze, [">= 1.1.7", "~> 1.1"])
      s.add_runtime_dependency(%q<terminal-notifier>.freeze, ["= 2.0.0"])
      s.add_runtime_dependency(%q<dotenv>.freeze, [">= 2.1.1", "~> 2.1"])
      s.add_runtime_dependency(%q<daemons>.freeze, [">= 1.2.3", "~> 1.2"])
      s.add_runtime_dependency(%q<os>.freeze, [">= 0"])
      s.add_development_dependency(%q<pry>.freeze, [">= 0"])
    else
      s.add_dependency(%q<thor>.freeze, [">= 0.20.0", "~> 0.20"])
      s.add_dependency(%q<gem_update_checker>.freeze, [">= 0.2.0", "~> 0.2.0"])
      s.add_dependency(%q<docker-compose>.freeze, [">= 1.1.7", "~> 1.1"])
      s.add_dependency(%q<terminal-notifier>.freeze, ["= 2.0.0"])
      s.add_dependency(%q<dotenv>.freeze, [">= 2.1.1", "~> 2.1"])
      s.add_dependency(%q<daemons>.freeze, [">= 1.2.3", "~> 1.2"])
      s.add_dependency(%q<os>.freeze, [">= 0"])
      s.add_dependency(%q<pry>.freeze, [">= 0"])
    end
  else
    s.add_dependency(%q<thor>.freeze, [">= 0.20.0", "~> 0.20"])
    s.add_dependency(%q<gem_update_checker>.freeze, [">= 0.2.0", "~> 0.2.0"])
    s.add_dependency(%q<docker-compose>.freeze, [">= 1.1.7", "~> 1.1"])
    s.add_dependency(%q<terminal-notifier>.freeze, ["= 2.0.0"])
    s.add_dependency(%q<dotenv>.freeze, [">= 2.1.1", "~> 2.1"])
    s.add_dependency(%q<daemons>.freeze, [">= 1.2.3", "~> 1.2"])
    s.add_dependency(%q<os>.freeze, [">= 0"])
    s.add_dependency(%q<pry>.freeze, [">= 0"])
  end
end
