# ublock_filters

<img src="assets/icon.svg" width="64" height="64" alt="">

A collection of personal filter lists for **uBlock Origin on Firefox**. Each file
customizes a particular site, so you can subscribe to the lists you want. The current
lists cover Marktplaats; more sites can be added independently.

## Available filters

| Filter                                                     | Site and exclusions                                                                                                                              | Subscription                                                                                     |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| [Marktplaats promotional cleanup](filters/marktplaats.txt) | marktplaats.nl: Topadvertenties, dagtoppers, Admarkt listings, promotional stickers and advertising clutter.                                     | [Raw list](https://raw.githubusercontent.com/royvou/ublock_filters/main/filters/marktplaats.txt) |
| [Marktplaats optional cleanup](filters/optional.txt)       | marktplaats.nl: Reserved listings, related recommendations and “Ook van deze adverteerder” strips. Works on its own or with promotional cleanup. | [Raw list](https://raw.githubusercontent.com/royvou/ublock_filters/main/filters/optional.txt)    |

## Install

1. Open uBlock Origin → **Dashboard** → **Filter lists**.
2. Under **Custom** → **Import**, paste the raw subscription URL from the table.
3. Click **Apply changes**, then reload the affected site.

Keep cosmetic filtering, automatic list updates and your usual advertising lists
enabled. Use the full uBlock Origin extension; uBlock Origin Lite is not supported. To
disable a subscription, uncheck it in **Filter lists** and apply changes.

You can also paste a file into **My filters** and apply changes. Pasted rules need
manual updates. These lists hide content and do not inherently prevent its network
requests. Site-specific effects and limitations are documented separately.

## Contribute

Found missed content or something hidden by mistake? Open an issue with the site URL,
enabled filter files and a screenshot. See [CONTRIBUTING.md](CONTRIBUTING.md) for adding
sites, changing rules and validation, and [CHANGELOG.md](CHANGELOG.md) for release
notes.

[MIT licensed](LICENSE).
