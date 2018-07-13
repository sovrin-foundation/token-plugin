# GemUpdateChecker
[![Build Status](https://travis-ci.org/henteko/gem_update_checker.svg?branch=master)](https://travis-ci.org/henteko/gem_update_checker)
[![Gem Version](https://badge.fury.io/rb/gem_update_checker.svg)](https://badge.fury.io/rb/gem_update_checker)

This gem is gem update check.


## Installation

Add this line to your application's Gemfile:

```ruby
gem 'gem_update_checker'
```

And then execute:

    $ bundle

Or install it yourself as:

    $ gem install gem_update_checker

## Usage

```ruby
require 'gem_update_checker'

gem_name = 'your_gem_name'
current_version = '0.0.1'
checker = GemUpdateChecker::Client.new(gem_name, current_version)

if checker.update_available
  puts "#{gem_name} #{checker.latest_version} is available"
  puts "please run gem update #{gem_name}"
end
```

## Contributing

Bug reports and pull requests are welcome on GitHub at https://github.com/henteko/gem_update_checker.

## License
MIT
