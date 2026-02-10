# typescript-multiple-package-versions example

This example shows how to consume multiple versions of the emissions-calculators package at the same time from NPM. Over time, more versions will be published and available. If you want to build an application that can use multiple published versions of the packages, you will need to consider that each version will have different inputs and outputs.

# Configuration

The basic approach is to use NPM [aliases](https://docs.npmjs.com/cli/v8/using-npm/package-spec#aliases) to import multiple versions of the same package name.

```
  "dependencies": {
    "@aginnovationaustralia/emissions-calculators3.0.0": "npm:@aginnovationaustralia/emissions-calculators@^3.0.0",
    "@aginnovationaustralia/emissions-calculators3.0.1": "npm:@aginnovationaustralia/emissions-calculators@^3.0.1"
  }

```

The alias you choose to create is quite flexible, for example:

```

  "dependencies": {
    "calcV300": "npm:@aginnovationaustralia/emissions-calculators@^3.0.0",
    "calcV301": "npm:@aginnovationaustralia/emissions-calculators@^3.0.1"
  }

```

Then you just import from the alias you create. If you're importing from multiple aliases within the same file, you'll probably want to choose some unique import names to avoid collisions:

```
import {
  BeefInput as BeefInput300,
  BeefOutput as BeefOutput300,
  calculateBeef as calculateBeef300,
} from "@aginnovationaustralia/emissions-calculators3.0.0";
import {
  BeefInput as BeefInput301,
  BeefOutput as BeefOutput301,
  calculateBeef as calculateBeef301,
} from "@aginnovationaustralia/emissions-calculators3.0.1";
```

# Wrapping multiple versions of a calculator

If you want to create a single function that can call different versions of the same calculator, keep in mind that the inputs will be different for each different version. A simple example that maintains TypeScript correctness is:

```
function calculateBeefWithVersion<
  V extends "3.0.0" | "3.0.1",
  I extends V extends "3.0.0" ? BeefInput300 : BeefInput301
>(version: V, input: I): V extends "3.0.0" ? BeefOutput300 : BeefOutput301 {
  if (version === "3.0.0") {
    return calculateBeef300(input);
  } else {
    return calculateBeef301(input);
  }
}
```
