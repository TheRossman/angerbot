require 'rest-client'

r = RestClient.post "https://badsyntax.slack.com/api/channels.list",
                    {
                        :token => 'xoxb-14562483251-elu5ImDgLBC04iRqXgIrH4LT'
                    }
r = JSON.parse(r)
r['channels'].each do |c|
  puts "#{c['name']} - id: #{c['id']}"
end