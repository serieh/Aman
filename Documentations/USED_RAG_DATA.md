# Aman RAG System: Knowledge Base & Data Sources

This document details the exact data sources, clinical guidelines, textbooks, and regional protocols embedded into the Qdrant Vector Database to power Aman's Retrieval-Augmented Generation (RAG) system. These resources serve as the factual grounding that prevents the LLM from hallucinating clinical advice.

## 1. Psychology & Counseling Textbooks (Therapeutic Reasoning)
* **Cognitive Behavioral Therapy: Basics and Beyond (2nd Edition)** — Judith Beck
* **Motivational Interviewing (2nd Edition)** — Miller & Rollnick (Critical for guiding resistant users)
* **Dialectical Behavior Therapy Skills Training (2nd Edition)** — Marsha Linehan (Emotional regulation)
* **A Guide to Rational Living** — Albert Ellis (REBT framework)
* **OpenStax Psychology** (Full peer-reviewed textbook)
* **Introduction to Psychology** (Saylor Academy)
* **The Principles of Psychology (Volumes 1 & 2)** — William James

## 2. Mental Health Guidelines & Clinical Protocols (Ethical Boundaries)
* **DSM-5-TR** (Diagnostic descriptions only — used strictly for pattern recognition to appropriately refer users to clinical professionals, not for autonomous diagnosis)
* **ICD-11** (Mental and Behavioural Disorders chapter)
* **WHO mhGAP Intervention Guide (Version 2.0)** (Community-level mental health protocols)
* **Mental Health Atlas 2024** (WHO)
* **APA Clinical Practice Guidelines** (Specifically for the treatment of Depression and PTSD)
* **IASP (International Association for Suicide Prevention)** (Safe messaging guidelines)
* **Regional Mental Health Protocols**: Psychiatric Mental Health Nursing Scope of Practice and Competencies

## 3. Crisis Intervention & Safety Protocols (De-escalation & Harm Prevention)
* **Columbia Suicide Severity Rating Scale (C-SSRS)** (Utilized to understand and measure conversational escalation levels)
* **LEADERS Suicide Prevention Safe Messaging Guide** (AFSP and IASP)
* **Crisis Text Line De-escalation Frameworks** ("Assessing effective de-escalation of crisis conversations using transformer-based models")
* **National Strategy for Suicide Prevention** (HHS / CAMS Framework)
* **AFSP Safe Messaging Guidelines**

## 4. Therapeutic Techniques & Coping Strategies (Practical Tools)
* **Therapist Aid Worksheets** (CBT thought records, cognitive restructuring exercises)
* **Palouse Mindfulness-Based Stress Reduction (MBSR) Manual**
* **Dialectical Behavior Therapy** (General psychoeducation and distress tolerance content)

## 5. Psychoeducation & Plain-Language Mental Health Content
* **WHO Mental Health Fact Sheets** (Public-facing clinical explainers on anxiety, depression, and grief)

## 6. Regional & Islamic Sensitivity Data (MENA Context)
* **دليل تدخلات برنامج رأب الفجوة في الصحة النفسية** (mhGAP Arabic Translation)
* **WHO Eastern Mediterranean Region Mental Health Strategies** (Regional Policy Strategy)
* **Establishing a national substance use treatment information system: A step-by-step guide** (EMRO/WHO)
