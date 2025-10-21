# Privacy Policy

**Effective Date**: October 22, 2025
**Version**: 1.0

---

## 1. Data Collection & Usage Policy

### 1.1 Data We Collect

#### Input Data
- **Deliverable Names**: Names of deliverables for estimation
- **Deliverable Descriptions**: Detailed descriptions of deliverables
- **System Requirements**: Project system requirements (optional)
- **Question Answers**: Answers to questions for improving estimation accuracy

#### System Logs
- **API Access Logs**: Request ID, endpoint, response time
- **Error Logs**: Error type, timestamp, stack trace
- **Performance Metrics**: Processing time, OpenAI API usage (tokens, latency)

### 1.2 Purpose of Use

1. **Project Estimation Generation**: Automatic effort and cost estimation using AI (OpenAI GPT-4)
2. **Service Quality Improvement**: Improvement of estimation accuracy, system performance optimization
3. **Error Analysis & Improvement**: Investigation of system failures, bug fixes
4. **System Monitoring & Operations**: Real-time monitoring, anomaly detection, log analysis

### 1.3 Data We Do NOT Collect

We do not collect the following data:

- **Personally Identifiable Information (PII)**: Name, address, phone number, email address
- **Confidential Information**: Credit card information, passwords, national ID numbers
- **Tracking Cookies**: User behavior tracking, advertising cookies

---

## 2. Data Retention Period

| Data Type | Retention Period | Deletion Method |
|-----------|------------------|-----------------|
| **Estimation Task Data** | **30 days** | Auto-deletion or User deletion API |
| **System Logs** | **90 days** | Auto-deletion (log rotation) |
| **Metrics** | **30 days** | Auto-deletion |

### 2.1 Automatic Deletion

- **Estimation Task Data**: Automatically deleted 30 days after creation (runs daily at 2:00 AM)
- **System Logs**: Automatically rotated after 90 days
- **Metrics**: Automatically deleted after 30 days

### 2.2 User-Initiated Deletion

- **Deletion API**: Can be deleted anytime via `DELETE /api/v1/tasks/{task_id}`
- **Deletion Scope**: All data related to the task (deliverables, Q&A pairs, estimates, chat messages, files)

---

## 3. Third-Party Data Sharing

### 3.1 OpenAI API

- **Purpose**: Estimation generation, question generation, adjustment proposal generation
- **Data Shared**: Deliverable names, descriptions, system requirements, question answers
- **PII Protection**: PII detection & masking feature automatically excludes personal information
- **Data Retention**: Complies with OpenAI's data usage policy (https://openai.com/policies/usage-policies)
- **Data Deletion**: Data sent via OpenAI API is processed according to OpenAI's policy

### 3.2 Other Third Parties

**We do not share data with any other third parties.**

---

## 4. User Rights

### 4.1 Right to Access

- **API**: Access your estimation data via `GET /api/v1/tasks/{task_id}`
- **Privacy Information**: Check data retention period and auto-deletion date via `GET /api/v1/tasks/{task_id}/privacy`

### 4.2 Right to Erasure (Right to be Forgotten)

- **API**: Delete your estimation data anytime via `DELETE /api/v1/tasks/{task_id}`
- **Deletion Scope**: Deletes all data including tasks, deliverables, Q&A pairs, estimates, chat messages, and related files
- **Immediate Deletion**: Data is deleted immediately after API request

### 4.3 Right to Data Portability

- **Excel Export**: Download estimation data in Excel format (`GET /api/v1/tasks/{task_id}/download`)
- **Format**: Excel (.xlsx) format, importable to other systems

---

## 5. GDPR Compliance

### 5.1 Data Minimization

- **Minimal Data Collection**: Only collect data necessary for estimation generation
- **Automatic Deletion**: Automatically deleted after 30 days

### 5.2 Consent

- **Consent at Service Start**: Obtain consent to privacy policy
- **Explicit Data Processing**: Clearly state collected data, purpose of use, and third-party sharing

### 5.3 Transparency

- **Explicit Purpose of Use**: Stated in this policy
- **Third-Party Disclosure**: OpenAI API usage disclosed
- **Privacy Information**: API provides data retention period and auto-deletion date

### 5.4 Security

- **Environment Variable API Key Management**: OpenAI API key securely managed via environment variables
- **HTTPS Communication**: Encrypted communication via HTTPS in production environment
- **Access Logging**: All API access is logged
- **PII Detection & Masking**: Automatic detection and masking of personal information

---

## 6. Security Measures

### 6.1 Communication Security

- **SSL/TLS Encryption (HTTPS)**: Communication encrypted via HTTPS in production environment
- **Certificate Verification**: SSL certificate validity verified

### 6.2 Authentication & Authorization

- **Environment Variable API Key Management**: OpenAI API key securely managed via environment variables (`.env`)
- **Access Control**: Appropriate file access permissions

### 6.3 Input Validation

- **Guardrails**: Prompt injection protection, input validation
- **Sanitization**: SQL injection, command injection protection
- **PII Detection & Masking**: Exclusion of personal information from logs

### 6.4 Monitoring & Observability

- **Structured Logging**: JSON-formatted structured logs for monitoring
- **Metrics Collection**: OpenAI API usage, response time, error rate collection
- **Alerts**: Automatic alerts on anomaly detection

---

## 7. Contact Information

For privacy-related inquiries:

- **X (Twitter)**: [@realdaishiro](https://x.com/realdaishiro)
- **Response Time**: Weekdays 9:00-17:00 (Japan Time)

---

## 8. Privacy Policy Updates

This privacy policy may be updated from time to time to reflect changes in laws or service content.

- **Update Notification**: Important changes will be notified via the service
- **Effective Date**: Updated policy applies from the effective date

---

**Revision History**:
- **October 22, 2025**: Initial version (Version 1.0)

---

© 2025 AI Estimator System. All rights reserved.
