# AI Estimation System Safety Policy

## 1. Overview

This policy provides guidelines for the safe and responsible operation of the AI Estimation System.

This system leverages Large Language Models (LLMs) to generate estimates for system development projects. The goal is to maximize the capabilities of AI while ensuring safety, transparency, and privacy protection.

## 2. Core Principles

### 2.1 Integrity

- Provide accurate and well-founded estimates
- Explicitly state uncertainties when present
- Avoid misleading expressions
- Clearly show the rationale for effort and cost

### 2.2 Transparency

- Explicitly state that content is AI-generated
- Provide estimation rationale
- Explain system limitations
- Provide users with sufficient information

### 2.3 Privacy Protection

- Do not collect, store, or use PII (Personally Identifiable Information)
- Use user data only for estimation purposes
- Delete data after an appropriate period
- Follow the data minimization principle

### 2.4 Safety

- Do not generate or accept harmful content
- Follow security best practices
- Prevent prompt injection attacks
- Conduct continuous monitoring and improvement

## 3. Prohibited Content

The system will not generate or accept the following content:

### 3.1 Harmful Content

- Illegal, violent, or threatening content
- Discriminatory or defamatory content
- Sexually explicit content
- Harassing content
- Hate speech

### 3.2 Fraudulent Operations

- Unjustifiably high or low estimates
- Baseless price manipulation
- Intentional misinformation
- System abuse

### 3.3 Privacy Violations

- Requesting personal information (names, email addresses, phone numbers, etc.)
- Leaking confidential information
- Tracking or surveillance
- Unauthorized data collection

## 4. Rejection Criteria

The system will automatically reject processing in the following cases:

### 4.1 Input Rejection

Inputs meeting the following conditions will be rejected:

- **Toxicity score of 0.8 or higher**: High score from toxicity detection API
- **Prompt injection pattern detected**: Attempts to tamper with system prompts
- **Input length exceeds 10,000 characters**: Excessively long input
- **Invalid file format**: Files other than .xlsx or .csv
- **File size limit exceeded**: Files larger than 10MB
- **Input contains PII**: Email addresses, phone numbers, credit card numbers, etc.

### 4.2 Output Rejection

Outputs meeting the following conditions will be discarded and regenerated or rejected:

- **Output contains PII**: Leakage of personal information
- **Toxicity score of 0.8 or higher**: Inappropriate language
- **Schema validation failure**: Violation of estimation format
- **Business rule violation**: Effort out of range (0-1000 person-months), unit price out of range, etc.

## 5. Escalation Procedures

### 5.1 Response to Rejection

When processing is rejected, follow these steps:

1. **Return clear error message to user**: Do not include technical details, provide improvement suggestions
2. **Log rejection reason**: For security auditing
3. **Notify administrator for repeat violations**: Detect malicious attempts

### 5.2 Error Message Principles

- Do not include technical details (to avoid security risks)
- Clearly present improvement methods
- Provide support contact information
- Use user-friendly language

### 5.3 Incident Response

When a security incident occurs:

1. Record incident
2. Assess impact scope
3. Stop system if necessary
4. Investigate cause
5. Develop preventive measures
6. Notify users (if applicable)

## 6. Monitoring and Review

### 6.1 Continuous Monitoring

- **Regular review of rejected inputs/outputs**: Weekly verification
- **Analysis and improvement of false positives**: Adjust thresholds, add whitelist
- **Regular policy updates**: Review quarterly
- **Response to new threats**: Track security trends

### 6.2 Metrics

Continuously monitor the following metrics:

- Rejection rate (by input/output)
- Distribution of rejection reasons
- False positive rate
- Response time
- LLM API cost

### 6.3 Review Meetings

Hold safety policy review meetings quarterly to discuss:

- Analysis of rejection cases
- Need for policy updates
- Identification of new risks
- Improvement proposals

## 7. Compliance

### 7.1 Data Protection Regulations

- **GDPR**: Compliance with General Data Protection Regulation
- **Personal Information Protection Law**: Compliance with Japanese law
- **Data minimization**: Collect only minimum necessary data
- **Data retention period**: Delete 30 days after task completion

### 7.2 Security Standards

- **OWASP LLM Top 10**: Address LLM security risks
  - LLM01: Prompt Injection → Guardrails implemented
  - LLM02: Insecure Output Handling → Output validation implemented
  - LLM03: Training Data Poisoning → Input validation implemented
  - LLM06: Sensitive Information Disclosure → PII detection implemented
- **Regular security audits**: Conducted twice annually

### 7.3 AI Ethics

- **Fairness**: Do not generate discriminatory estimates
- **Accountability**: Clearly state estimation rationale
- **Human oversight**: Final decisions made by humans
- **Transparency**: Clearly state AI limitations

## 8. User Responsibilities

Users have the following responsibilities:

- Use the system only for appropriate purposes
- Do not input personal information
- Verify generated estimates
- Make final decisions as humans
- Report inappropriate use

## 9. Disclaimer

- This system is an AI-powered estimation support tool and does not guarantee the accuracy of estimates
- Final estimation decisions require verification by experts
- System outputs should be treated as reference information

## 10. Contact Information

For safety-related inquiries and incident reports, please contact:

- Security Officer: [Contact]
- System Administrator: [Contact]

---

**Effective Date**: 2025-10-18
**Revision History**:
- 2025-10-18: Initial draft created
- 2025-10-20: Officially effective based on Implementation

**Approver**: [Approver Name]
**Document ID**: SAFETY-POLICY-001
