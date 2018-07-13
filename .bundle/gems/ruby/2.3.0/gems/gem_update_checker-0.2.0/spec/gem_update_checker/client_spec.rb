describe GemUpdateChecker::Client do
  let(:name) {'gem_name'}
  let(:latest_version) {'1.0.0'}
  let(:response) {{:version => latest_version}}

  before do
    stub_request(:get, "#{GemUpdateChecker::Client::RUBYGEMS_API}/#{name}/latest.json").
        to_return(:body => response.to_json)
  end

  it "invalid version" do
    expect{
      GemUpdateChecker::Client.new(name, 'invalid version')
    }.to raise_error ArgumentError
  end

  context "update available" do
    it "current version is latest" do
      checker = GemUpdateChecker::Client.new(name, latest_version)
      expect(checker.update_available).to be_falsey
      expect(checker.latest_version).to eq latest_version
    end

    it "update available" do
      checker = GemUpdateChecker::Client.new(name, '0.0.1')
      expect(checker.update_available).to be_truthy
      expect(checker.latest_version).to eq latest_version
    end
  end
end
