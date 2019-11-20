# Installation

```
cd <you_django_project>
git submodule add <this_project_git_url>
git submodule init
git submodule update
```

# Settings

in Django settings add
```
WALLET_URL = 'https://<wallet_url>/'
WALLET_TOKEN = '<WALLET_API_TOKEN>'
```

In case you have many tokens and services, you can initial WALLET_TOKEN like this
```
WALLET_TOKEN = {
    'default': '<Default TOKEN>',
    'voip': '<TOKEN for VOIP>',
    'sqool': '<TOKEN for sqool>',
}
```
