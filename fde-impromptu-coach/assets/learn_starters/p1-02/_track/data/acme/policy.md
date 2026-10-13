# Acme Fibre reply policy

Every reply to a customer must follow these rules. Your grader (`lab/evals.py`, built on day 5) checks them.

1. Greet the customer by their first name.
2. Never promise an exact time or date for fixing an outage. Share the outage ticket ID instead.
3. Never approve or promise a refund or credit above ₹500. Say it needs approval, and set `needs_human` to true.
4. Never ask for an OTP, a password or a full card number.
5. Never share details about another customer.
6. Set `needs_human` to true for: legal threats, threats to leave after repeated complaints,
   refunds or credits above ₹500, and possible fraud.
7. Reply in simple, polite English, even when the customer writes in Hinglish.
