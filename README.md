# Example clients for working with the AIA Emissions Calculators API

The [AIA Environmental Accounting Platform (EAP)](https://www.aiaeap.com/) is an on-farm GHG emissions calculation engine developed by [Agricultural Innovation Australia](https://aginnovationaustralia.com.au). Free access to AIA’s open-source code is supported by the Australian Government through funding from the _Improving Consistency of On-Farm Emissions Estimates Program_.

This repo contains examples and sample code that make it easy to start working with the Emissions Calculators REST API that is part of the AIA EAP.

<p align='center'>
  <a href='https://aginnovationaustralia.com.au'>
    <img src='./assets/logo-light.svg' alt='Agricultural Innovation Australia' />
  </a>
</p>

# Examples

The repo currently includes fully documented and automatically generated API clients for C#, JavaScript, PHP and Python. See each example folder for detailed documentation. The goal is to supply scripts that allow you to either:
- use the source code in the example clients straight away
- code generate your own client for working with the API

Each example has a script that can run and execute a successful calculation, they typically just require configuring your client certificate files. They also include a script that is generating the client directly from the OpenAPI file for the API.

# Generation of client code

The generation of each language client is designed to be easy to reproduce and regenerate by anyone. Each example folder has a `generate.sh` script that should run cleanly out of the box. The scripts now accept the version as a first argument, and the calculator name as the second. The repo has a client generated for the beef calculator. If you want to generate a client for another calculator, run the generate script with your desired calculator name. For example, to generate the files for the `all-modules` calculator:

```
cd examples/c-sharp-api-client
./generate.sh 4.0.2 all-modules
```

# Contributing and support

If you are looking for help using the tools available here, there are a number of resources available to you.

First of all, we aim to make the tools as easy to use as possible out of the box, and for users to be able to self service their own questions. Documentation for consuming the REST API is available online [here](https://docs.aiaplatform.com.au).

If you still have a question, feel free to [open a github issue](https://github.com/aginnovationaustralia/emissions-calculators-examples/issues/new) and fill in the template with as much context as possible. We aim to have a response to your question within 48 hours.

# License

![Creative Commons Attribution](./assets/by.png)

This project is licensed under a [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/) license.

All users of the Code must acknowledge AIA as the source and maintainer of the EAP Calculator Engine code. All users of the Code must acknowledge that free access to the Code is supported by the Australian Government through funding from the Improving Consistency of On-Farm Emissions Estimates Program.

The acknowledgement must be displayed in documentation, digital interfaces, or product materials where attribution of technical components is ordinarily provided.

This includes the right to display the [‘Powered by EAP’](https://www.aiaeap.com/branding) logo in any systems which directly or indirectly use the open-source code, in a way which is clearly visible to third-party clients/customers/users of those systems.

At a minimum, the acknowledgement must state:

> “This product incorporates the EAP Calculator Engine open-source code developed and maintained by Agricultural Innovation Australia Ltd. Free access to AIA’s open-source code is supported by the Australian Government through funding from the Improving Consistency of On-Farm Emissions Estimates Program”

Users may not imply or state endorsement by AIA, unless explicit written consent from AIA has been granted. Users must not imply or state endorsement by the Australian Government.

---

<p align="center">
Made with ❤️ by
</p>

<p align="center">
    <a href="https://exogee.com">
        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="./assets/exogee-white.svg">
            <img src="./assets/exogee-black.svg" alt="Exogee">
        </picture>
    </a>
</p>
