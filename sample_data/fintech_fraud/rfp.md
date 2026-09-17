# Request for Proposal — Real-Time Payment Fraud Prevention Engine

## 1. Client Details & Industry Context

Global Payments Inc. is a leading global fintech company processing billions of transactions annually across diverse payment channels, including credit, debit, ACH, and emerging real-time payment rails. We operate in a highly regulated environment, and maintaining the integrity and security of transactions is paramount. Our extensive merchant network and consumer base demand robust, uninterrupted services.

## 2. Background & Problem Statement

Our current fraud detection systems are predominantly rule-based, which, while effective against known threats, struggles with the velocity and sophistication of modern fraud schemes. This leads to a high volume of false positives, necessitating significant manual review effort by our fraud analysts. We are experiencing increasing financial losses due to emerging sophisticated fraud patterns, particularly in areas like account takeover (ATO), synthetic identity fraud, and real-time payment scams. Furthermore, the slow adaptation of our current system to new threat vectors results in reputational damage and a suboptimal customer experience when legitimate transactions are erroneously blocked. We require a more adaptive, real-time solution to proactively combat these evolving threats.

## 3. Explicit Requirements

1.  **Real-Time Processing:** The proposed engine must be capable of processing payment transactions in real-time, delivering fraud scores and decisions with a sub-100ms latency. This includes ingestion, analysis, and decisioning for high-volume environments.
2.  **Advanced Analytics & ML/AI:** The solution must utilize advanced analytics, machine learning (ML), or artificial intelligence (AI) models to identify complex and evolving fraud patterns. The primary goal is to significantly reduce false positives (target reduction of at least 30%) while maintaining or improving fraud detection rates.
3.  **Case Management System:** A robust and intuitive case management system for fraud analysts is required. This system should facilitate alert review, investigation workflow management, and provide mechanisms for analysts to provide feedback for continuous model improvement and training.
4.  **Reporting & Analytics:** Comprehensive reporting and analytics capabilities are essential. This includes dashboards for real-time fraud trends, historical loss attribution, model performance metrics (e.g., precision, recall, F1-score), and customizable reporting for compliance and internal stakeholders.
5.  **High Availability & Scalability:** The system must guarantee high availability (target 99.99%) and demonstrate proven scalability to handle peak transaction volumes of up to 5,000 transactions per second (TPS) without performance degradation.
6.  **API Integration:** The solution must provide clear, well-documented APIs (RESTful preferred) and SDKs for seamless integration with our existing core banking platforms, payment gateway systems, and internal data lakes.
7.  **New Account & Account Takeover Fraud (NAF/ATO):** A dedicated module or specialized capabilities for identifying and mitigating new account fraud (NAF) and account takeover (ATO) attempts across various digital channels are required.

## 4. Critical Negative Constraint

**The solution MUST be deployed on-premise within our existing data centers. Furthermore, it MUST integrate directly with our existing PostgreSQL database cluster for historical transaction data and customer profiles. NO public cloud deployments or database migrations are permitted under any circumstances for this project phase.**

## 5. Budget Range

The total budget allocated for this project, including software licensing, implementation services, customization, training, and 1st year support and maintenance, is capped at **€250,000 – €350,000.**

## 6. Timeline Expectations

We expect a working pilot/proof-of-concept (PoC) deployed in a User Acceptance Testing (UAT) environment within **3 months** of contract signing. Full production rollout across our primary payment channels and integration points is expected within **6 months** of contract signing.
