# coding: utf-8
lib = File.expand_path('../lib', __FILE__)
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
require 'gem_update_checker/version'

Gem::Specification.new do |spec|
  spec.name          = "gem_update_checker"
  spec.version       = GemUpdateChecker::VERSION
  spec.authors       = ["henteko"]
  spec.email         = ["henteko07@gmail.com"]

  spec.summary       = %q{Check gem update.}
  spec.description   = %q{Check gem update.}
  spec.homepage      = "https://github.com/henteko/gem_update_checker"
  spec.license       = "MIT"

  spec.files         = `git ls-files`.split($/)
  spec.executables   = spec.files.grep(%r{^bin/}) { |f| File.basename(f) }
  spec.test_files    = spec.files.grep(%r{^(test|spec|features)/})
  spec.require_paths = ["lib"]

  spec.add_development_dependency "bundler", "~> 1.10"
  spec.add_development_dependency "rake", "~> 10.0"
  spec.add_development_dependency "rspec", "~> 3.3.0"
  spec.add_development_dependency "webmock", "~> 1.21.0"
end
