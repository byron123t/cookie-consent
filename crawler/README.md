# Cookie Consent Project.

Research project about online cookie consent.


## consent-scan

The kernel produces 3 things: `consent_resources.json`, `log.json` (contains category-based consent), and traffic har file (contains cookie flows).
`consent_resources.json` combines with `log.json` produces consent of each cookie.
Comparing the per-cookie consent with the cookie flows in the traffic har file, we will know the consistency.

