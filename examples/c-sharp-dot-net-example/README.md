# C# Integration Test

This is a .NET core project which makes a certificate authenticated request to the EAP API.

## To Run

```console
$ dotnet run
```

## The Request

This example uses a hard coded request in `ExampleRequest.cs`. In a real integration, this would be derived from data within your system.

## Mutual TLS

The API uses mutual TLS. A PEM encoded certificate and private key needs to be supplied in the `certificates` directory. Read the README.md file in that directory for more information.

## Server Certificate Validation

To validate that the certificate is coming from the EAP platform, perform the following verification:

- A certificate must have been presented by the server.
- It has not expired.
- The Subject of the certificate is `CN=*.aiaapi.com`.
- It is valid and trusted by the operating system trust store (e.g. `certificate.Verify()` returns `true`).

Example code to perform this validation is in [Program.cs](./Program.cs).
