# Security

## Reporting

If you believe you found a security issue in **this repository’s code** (not in Google NotebookLM or third-party MCP servers), please open a **private** security advisory on GitHub if available, or contact the maintainer directly. Do not post exploit details in public issues.

## Scope

This project is a **local orchestration tool**. It does not provide multi-user authentication or a hardened server boundary by default. Running FastAPI or Streamlit on `127.0.0.1` is recommended for local use.

## Sensitive data

- Never commit `.env` or session/auth artifacts from `notebooklm-mcp` or browser automation.
- Prefer a **dedicated Google account** for any NotebookLM automation workflows.

## Third parties

NotebookLM, `notebooklm-mcp`, and Cursor MCP are **third-party** systems. Their security posture and terms of use are outside this repo’s control.
