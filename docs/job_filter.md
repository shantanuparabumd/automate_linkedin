# Job Filters Configuration (`job_filters.yaml`)

This file defines the criteria and filters for searching and ranking jobs. Customize this file based on your job search preferences.

---

## Structure of `job_filters.yaml`

### **1. Keywords**
These are the main keywords that the script uses to search for jobs. Combine relevant terms that match your desired roles.

```yaml
keywords: 
  - "Machine Learning"         # Example: Jobs in ML-related fields.
  - "Robotics"                 # Example: Robotics-related roles.
  - "Software Developer"       # General software development positions.
```

---

### **2. Max Jobs**
Specify the maximum number of jobs to scan in one run.

```yaml
max_jobs: 200                  # Default: 200 jobs.
```

---

### **3. Description Filters**
Filters for scoring job descriptions. Use these to prioritize or exclude jobs based on keywords.

#### Positive Keywords
These keywords increase the job's score if they appear in the description.

```yaml
positive:
  - "Python"
  - "C++"
  - "ROS"
  - "Machine Learning"
  - "Reinforcement Learning"
  - "Robotics"
```

#### Negative Keywords
These keywords exclude a job if even one appears in the description or title.

```yaml
negative:
  - "Sales"
  - "10+ Years"
  - "Senior"
  - "PhD"
  - "Scientist"
```

#### Best Keywords
These keywords heavily prioritize jobs, significantly boosting their score.

```yaml
best:
  - "ROS"
  - "Reinforcement Learning"
```

**Important Note**:  
The presence of even a single negative keyword will exclude the job. Be cautious when adding generic terms like "lead," which might appear as a noun or verb.

---

### **4. Location**
Specify the location for job searches.

```yaml
location: "United States"      # Example: Jobs in the US.
```

---

### **5. Date Posted**
Filters jobs based on how recently they were posted.

```yaml
date_posted: "past_month"      # Options: past_24_hours, past_week, past_month
```

---

### **6. Job Type**
Filter jobs based on their type.

```yaml
job_type: 
  - "Full-time"
  - "Contract"
  - "Internship"
```

---

### **7. Work Mode**
Filter jobs by their work mode.

```yaml
work_mode:
  - "Remote"                   # Fully remote jobs.
  - "Hybrid"                   # Hybrid work mode.
  - "Onsite"                   # Onsite positions.
```

---

### **8. Experience Level**
Specify experience levels for filtering.

```yaml
experience_level:
  - "Entry level"
  - "Mid-Senior level"
```

---

### **9. Blacklisted Companies**
Exclude specific companies from the search.

```yaml
blacklisted_companies:
  - "Jobot"
  - "Dice"
  - "CompanyNameToAvoid"
```

---

## Example File

```yaml
keywords: 
  - "Machine Learning"
  - "Robotics"
  - "Software Developer"

max_jobs: 200

description:
  positive:
    - "Python"
    - "C++"
    - "ROS"
    - "Machine Learning"
    - "Reinforcement Learning"
    - "Robotics"

  negative:
    - "Sales"
    - "10+ Years"
    - "Senior"
    - "PhD"
    - "Scientist"

  best:
    - "ROS"
    - "Reinforcement Learning"

location: "United States"

date_posted: "past_month"

job_type: 
  - "Full-time"
  - "Contract"
  - "Internship"

work_mode:
  - "Remote"
  - "Hybrid"
  - "Onsite"

experience_level:
  - "Entry level"
  - "Mid-Senior level"

blacklisted_companies:
  - "Jobot"
  - "Dice"
```

---

## Tips for Customization

1. **Keyword Selection**  
   - Use specific terms to narrow down the search.
   - Avoid overly generic keywords to prevent irrelevant results.

2. **Positive and Negative Filters**  
   - Carefully curate these lists. Keywords like "lead" may exclude jobs with phrases like "Lead Engineer."

3. **Location and Work Mode**  
   - Use these to ensure jobs match your physical and logistical preferences.

4. **Blacklisted Companies**  
   - Avoid known irrelevant or undesirable companies.

For detailed explanations on other configuration files, refer to the main [README.md](../README.md).
