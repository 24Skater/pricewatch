# Security Policy

## Supported Versions

We actively support and provide security updates for the following versions of Pricewatch:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

We take the security of Pricewatch seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **Email**: Open a security advisory on GitHub (preferred)
   - Go to the [Security tab](https://github.com/pricewatch/pricewatch/security/advisories)
   - Click "Report a vulnerability"
   - Fill out the form with details about the vulnerability

2. **Private Contact**: If you cannot use GitHub, email the maintainers directly
   - Include a detailed description of the vulnerability
   - Include steps to reproduce the issue
   - Include potential impact assessment

### What to Include

When reporting a vulnerability, please include:

- **Type of vulnerability** (e.g., XSS, SQL injection, authentication bypass)
- **Affected component** (e.g., API endpoint, authentication system, scraper)
- **Steps to reproduce** the vulnerability
- **Potential impact** of the vulnerability
- **Suggested fix** (if you have one)
- **Proof of concept** (if applicable, but be careful not to cause damage)

### What to Expect

- **Initial Response**: We will acknowledge receipt of your report within 48 hours
- **Status Updates**: We will provide updates on the status of the vulnerability every 7 days
- **Resolution Timeline**: 
  - Critical vulnerabilities: 7 days
  - High severity: 14 days
  - Medium severity: 30 days
  - Low severity: 90 days

### Disclosure Policy

- We follow a **coordinated disclosure** process
- We will notify you when the vulnerability is fixed
- We will credit you in the security advisory (unless you prefer to remain anonymous)
- We will not disclose the vulnerability publicly until a fix is available
- We ask that you do not disclose the vulnerability publicly until we have released a fix

### Security Best Practices

When using Pricewatch in production:

1. **Keep dependencies updated**: Regularly update all dependencies
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Use strong secrets**: Generate strong, unique values for:
   - `SECRET_KEY` (minimum 64 characters)
   - `ENCRYPTION_KEY` (Fernet key)

3. **Enable HTTPS**: Always use HTTPS in production environments

4. **Configure security headers**: Ensure security headers are properly configured

5. **Monitor logs**: Regularly review application logs for suspicious activity

6. **Limit access**: Use firewall rules to restrict access to the application

7. **Regular backups**: Maintain regular backups of your database

8. **Environment isolation**: Use separate environments for development, staging, and production

### Known Security Features

Pricewatch includes the following security features:

- ✅ **Encryption at Rest**: Sensitive data (notification credentials) encrypted using Fernet
- ✅ **Input Validation**: Comprehensive validation of all user inputs
- ✅ **Rate Limiting**: Protection against brute force and abuse
- ✅ **CSRF Protection**: Cross-site request forgery protection on all forms
- ✅ **Security Headers**: X-Content-Type-Options, X-Frame-Options, CSP, etc.
- ✅ **SSRF Protection**: Server-side request forgery protection in URL validation
- ✅ **XSS Prevention**: Input sanitization and output encoding
- ✅ **SQL Injection Prevention**: Parameterized queries via SQLAlchemy ORM
- ✅ **Secret Masking**: Sensitive data redacted in logs
- ✅ **Request ID Tracking**: Full request lifecycle tracking for security auditing

### Security Audit

We regularly perform security audits:

- **Automated Scanning**: Bandit, Safety, and pip-audit run in CI/CD
- **Dependency Updates**: Dependencies are regularly updated
- **Code Review**: All code changes are reviewed for security issues
- **Penetration Testing**: Periodic security assessments

### Security Updates

Security updates are released as:

- **Patch releases** (e.g., 2.1.1) for critical security fixes
- **Minor releases** (e.g., 2.2.0) for security improvements and features
- **Major releases** (e.g., 3.0.0) for significant security architecture changes

### Security Checklist for Contributors

If you're contributing code, please ensure:

- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS prevention (sanitize/escape output)
- [ ] CSRF protection on state-changing operations
- [ ] Rate limiting on sensitive endpoints
- [ ] Proper error handling (no information leakage)
- [ ] Security headers included in responses
- [ ] Dependencies are up-to-date and secure
- [ ] Tests include security test cases

### Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

**Thank you for helping keep Pricewatch and its users safe!**

