# Secret Rotation Guide

If any credentials were accidentally committed to this repository:

1. **Revoke the exposed secret** from the service provider immediately.
2. **Generate a new credential** following your provider's recommended process.
3. **Update the new value** in the relevant secret management system (e.g. GitHub Secrets, Pulumi, environment variables).
4. **Commit a sanitized `.secrets.baseline`** and run `pre-commit` to ensure no further secrets are introduced.
5. **Force rotate dependent services** if necessary (e.g. restart deployments, invalidate tokens).

Always avoid storing plaintext secrets in source control. Use environment variables or secret managers instead.
