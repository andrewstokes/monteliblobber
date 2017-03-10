Monteliblobber
==============

A reasonable way to extract and contextualize network artifacts from blobs.

## Overview

Monteliblobber is simply a web UI driven network artifact parser that allows for IP address based threat intelligence integration.

I developed this tool to aid SOC analysts with automating some repetitive tasks. My fellow analysts and I found plenty of times where we needed to search through an arbitrary blob of something for network artifacts, and would inevitably need to determine the geo-location and blacklist status. After getting the beta version running we found ourselves using it for a [variety of things](#use-cases).

I thought other security analysts, researchers, and incident responders might find this tool beneficial, so I made it as easy as possible to setup and use by providing portable binary [distributions](#binary-distributions) for Mac and Windows.

### Features

- Identify and extract network artifacts.
    - IPv4 Addresses
    - FQDNs
    - URLs
    - Email Addresses
- Use a list of predefined tags/networks to tag arbitrary network addresses.
- Use a white list to filter out known uninteresting things from the results.
- Provide additional context to network addresses using Geo-Ip and blacklist lookups.
- Reasonably flexible blacklist customization. Thanks to our friends at [FireHol][1].
- A simple browser based UI.
    - Paste text blobs into the UI or select a file from the file system.
    - String based search/filtering.
    - Export to CSV or clipboard.
    - Supports processing ASCII or binary files.

## Getting Started

> DISCLAIMER: This application was not designed to run internet facing. This should go without saying considering the target audience, but don't be an idiot and run this on anything other than a loopback interface.

There are two methods you can use to get Monteliblobber running. I have provided portable executables built using PyInstaller for Mac and Windows, or you can download the source code from GitHub and run it from a terminal window.

## Binary Distributions

Using the portable binaries are the fastest and easiest way to use Monteliblobber. All the dependencies have been packaged in the executable, so there's no need to download anything extra. See the platform specific instructions below.

### Windows

Download the compressed executable from the [release page][8]. Unzip and double-click. A terminal window will appear in the background and your browser window will automatically open to Monteliblobber's home page. Terminate the application by selecting the terminal window and then pressing <kbg>Ctrl</kbg>+<kbg>C</kbg>.

### Mac

I built two different executables for Macs. The first is a typical Unix executable, and the other is a Mac application package. The Unix executable can be downloaded from the [release page][8] and run from a terminal window. The Mac application package can be downloaded and then copied to the `Applications` folder like a typical Mac application. I have not signed these executables, so you will likely need to approve the application in the security settings before it will be allowed to run. I have provided instructions on how to roll your own binary from the source if you don't feel comfortable running the ones I provided. It's okay, I understand.

> IMPORTANT: If you use the Mac application package, make sure to terminate the application using the `Quit` button on the right side of the nav bar. It runs in the background without exposing a terminal window, so you will have to force quit the app if you don't use the `Quit` button. 

### *Nix

I didn't roll a binary release for *Nix platforms. Use the [source distributions](#source-distributions) install instructions. 

## Source Distributions

Make sure Python 3 and Pip are installed, and then clone the GitHub repository.

```shell
git clone https://github.com/andrewstokes/monteliblobber.git
```

Change into the project directory.

```shell
cd monteliblobber
```

Install dependencies using pip.

```shell
pip install -r requirements.txt
```

### Running Tests

Use this command to test the application.

```shell
python -m unittest tests/test_monteliblobber.py
```

### Starting the Application

Move into the application directory and run the application:

```shell
cd Monteliblobber
python monteliblobber.py
```

The application will open your default browser window to the home page.

### Downloading Static Files

I didn't want to assume a user would want the application calling out automatically to download the initial static files. Therefore, an error will appear on the landing page the first time the app is run. Use the `Actions` menu to trigger the static file downloads and then refresh the page.

### Configuration

There are several settings you can change to tailor Monteliblobber to meet your specific needs. To change these settings you will need to create a config file named `monteliblobber.cfg` in Monteliblobber's local config directory. The local config directory is called `.monteliblobber` and will be located in the root of your user profile.

> INFO: An application restart is required after creating or changing the config file.

The following are the user configurable settings and application defaults. Simply paste these into the `monteliblobber.cfg` file and the defaults will be overridden at runtime.

#### USER_LABELED_NETWORKS

This allows for adding arbitrary networks and names to the analyzer. Any networks defined here will be tagged with the label provided as the key in the dictionary item. The config shown below would cause any address in the defined networks to be tagged as `GOOG` or `MSFT`.

```python
LABELED_NETWORKS = {
    'GOOG': ['209.85.192.0/24', '74.125.82.0/24', '8.8.8.8'],
    'MSFT': ['131.107.0.0/16', '207.46.0.0/16']
}
```

#### WHITELISTS

Any domains defined in the config will cause artifacts containing the domain to be discarded before the final results are sent to the UI. Any networks or addresses defined in this config will cause network addresses that match or are in a defined network to be discarded. The `domains` config shown below would cause all FQDNs or URLs with google or mircosoft domains to be removed from the results. The `network_addresses` config would cause the address `127.0.0.1` or any addresses in the `10.0.0.0/8` network to be removed.

```python
WHITELISTS = {
    'domains': ['google.com', 'microsoft.com', 'outlook.com'],
    'network_addresses': ['127.0.0.1', '10.0.0.0/8']
}
```

#### BLACKLISTS

Names and URLs for FireHol blacklists. The [FireHol][1] lists are currently the only lists supported. These are key-value mappings where the key is the name you want to appear in the results tag, and the value is the URL to the raw file on [FireHol's][2] GitHub repository. Feel free to change or add to these blacklists.

Unfortunately, I designed Monteliblobber to specifically process the [FireHol][1] `.ipset` and `.netset` blacklists. Fortunately, [FireHol][1] has been awesome enough to curate a ton of well known blacklists. I'm sure you can find something that suits your needs. Keep in mind, adding too many could negatively impact performance.

```python
BLACKLISTS = {
    'dshield_7D': 'https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/dshield_7d.netset',
    'bambenek_c2': 'https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/bambenek_c2.ipset',
    'alienvault': 'https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/alienvault_reputation.ipset'
}
```

#### AUTO_OPEN_BROWSER

Controls whether the app automatically opens the default browser window to Monteliblobber's home page.

```python
AUTO_OPEN_BROWSER = True
```

The application settings are located in the `monteliblobber/Monteliblobber/settings.py` file. Settings with the prefix `DEFAULT_` can be customized to meet your needs. Changing other settings could break something, so use caution.

## General Usage

![alt text](https://github.com/andrewstokes/monteliblobber/raw/development/docs/img/monteliblobber_home.png)

### Getting Data In

There are two primary methods of getting data in to be analyzed.

1. Paste - Select the Blob tab on the home page, and then paste the data in to the text box.

2. File Upload - Select the Upload tab, and then select the file to upload.

### Working with Results

Analysis results are presented in an interactive table. The idea is to use the sorting/filtering capabilities to find interesting records. The blacklist and geoip tags should help provide some extra context as you endeavor to identify interesting artifacts. You can delete uninteresting records and then dump the remaining records to a csv file/clipboard to use elsewhere. 

![alt text](https://github.com/andrewstokes/monteliblobber/raw/development/docs/img/monteliblobber_filter.png)

## Use Cases

These are some examples of how I use the program.

### Log Analysis

*Find Interesting Parts of a Log File Quickly*

On several occasions I have been sent some log files with the message "please check for evil" or some such nonsense.

I'll fire up Monteliblobber, open the log file with a text editor, copy the logs over to Monteliblobber, and then wait for the results.

> WARNING: Consider using the file upload method if you think the pasted data is larger than 5MB, or you may crash the browser.

Then I will usually remove some of the obvious "not evil" records to shrink the data set. Then sort or filter on tags to find interesting artifacts.
 
I also use this to post-process grep searches on logs. Use grep to find a bunch of interesting logs and then paste them into Monteliblobber for GeoIP and blacklist lookup.

### Convert Threat Intel Documents to Something Useful

Someone sends me a threat intel report in a PDF, Word Doc, email, etc. I copy the entire thing into Monteliblobber and let it pull all the indicators into a usable format.

### Malware and Process Memory

I've used Monteliblobber to quickly process stings that have been dumped from unpacked malware, static binaries, or process memory.

## Operational Security

A few opsec considerations.
 
- Monteliblobber will leave files in the `.monteliblobber` directory which will be created in the root of the user's profile directory.
- This application **does not** attempt to resolve any IPs or host names over DNS.
- The only network connections created by this application are when the user initiates an update of a static file through the UI. The outbound connections will go to either `iana.org`, `maxmind.com`, or `githubusercontent.com` depending on what action is selected.

## Creating a Binary from Source

This is actually a pretty simple process and I will provide the spec file template for both platforms. Regardless of the platform you intend to build on follow the source distribution [install instructions](#source-distributions). Next, follow the platform specific instructions.

> NOTE: I wanted to point out that the file hashes will not match between the official releases and the executables you compile. Don't be alarmed, this is expected behavior. For more information read the PyInstaller [documentation][12].

### Windows

Download and install the Microsoft Visual C++ 2010 Redistributable packages here [x86][9] and here [x64][10]. Next, use `pip` to install [PyInstaller][11].

```shell
pip install pyinstaller
```

Using a text editor, create a file named `monteliblobber.spec` in the root of the monteliblobber directory. Paste the following contents into the file.

```text
# -*- mode: python -*-

block_cipher = None

added_files = [
  ("Monteliblobber\\templates", "templates"),
  ("Monteliblobber\\static", "static"),
  ("Monteliblobber\\settings.py", "."),
]

a = Analysis(['Monteliblobber\\monteliblobber.py'],
             pathex=['C:\\Users\\admin\\Downloads\\monteliblobber'],  #<------- Change ME!!!
             binaries=[],
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['jinja2.asyncsupport','jinja2.asyncfilters'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='monteliblobber',
          debug=False,
          strip=False,
          upx=True,
          console=True,
          icon="docs\\img\\mtb.ico" )
```
 
Make sure to update the `pathex` value to match the path where you downloaded the monteliblobber repo. Navigate to the root of the repo using a terminal and execute the following command.

```shell
pyinstaller --onefile monteliblobber.spec
```

The output of the command will result in the creation the `build` and `dist` directories. The executable is located in the `dist` directory.

### Mac

Use `pip` to install [PyInstaller][11].

```shell
pip install pyinstaller
```

Using a text editor, create a file named `monteliblobber.spec` in the root of the monteliblobber directory. Paste the following contents into the file.

```text
# -*- mode: python -*-

block_cipher = None

added_files = [
  ("Monteliblobber/templates", "templates"),
  ("Monteliblobber/static", "static"),
  ("Monteliblobber/settings.py", "."),
]

a = Analysis(['Monteliblobber/monteliblobber.py'],
             pathex=['/Users/admin/Downloads/monteliblobber'],  #<------- Change ME!!!
             binaries=[],
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['jinja2.asyncsupport','jinja2.asyncfilters'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Monteliblobber',
          debug=False,
          strip=False,
          upx=True,
          console=False )
app = BUNDLE(exe,
             name='Monteliblobber.app',
             icon="docs/img/mtb.icns",
             bundle_identifier="com.monteliblobber.Monteliblobber",
             info_plist={
    'CFBundleShortVersionString': '1.0.0',
    'Minimum system version': '10.6'
})

```

Make sure to update the `pathex` value to match the path where you downloaded the monteliblobber repo. Navigate to the root of the repo using a terminal and execute the following command.

```shell
pyinstaller --onefile --windowed monteliblobber.spec
```

The output of the command will result in the creation the `build` and `dist` directories. The executable and application package are located in the `dist` directory.

## License

[MIT License](https://opensource.org/licenses/MIT)
 
## Attribution

### Maxmind

This application contains GeoLite2 data created by MaxMind, available from [MaxMind][3].

### DataTables.net

The interactive table in this application was built using the [DataTables.net][4] javascript libraries. Check this project out, fantastic work!

### Flask

The web application is served using [Flask][6].

### Requests

The downloader capability is powered by [Requests][5].

## Development

Please feel free to fork. I will be improving Monteliblobber as I have time.



[1]:https://iplists.firehol.org/
[2]:https://github.com/firehol
[3]:http://maxmind.com
[4]:http://datatables.net
[5]:https://github.com/kennethreitz/requests
[6]:https://github.com/pallets/flask
[7]:docs/img/monteliblobber_home.png
[8]:https://github.com/andrewstokes/monteliblobber/releases
[9]:https://www.microsoft.com/en-us/download/details.aspx?id=5555
[10]:https://www.microsoft.com/en-us/download/details.aspx?id=13523
[11]:https://pyinstaller.readthedocs.io
[12]:https://pyinstaller.readthedocs.io/en/stable/advanced-topics.html#creating-a-reproducible-build
