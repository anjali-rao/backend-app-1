REASONS = [
    'Customer unavailable',
    'Advisor unavailable',
    'Cheque incorrect',
    'Application incomplete',
    'High Age',
    'Abnormal BMI',
    'High Premium',
    'Past medical',
    'Customer unreachable',
    'Customer unavailable',
    'Underwriter Rejected',
    'Details incomplete',
    'Payment incomplete',
    'Query incomplete',
    'additional documents to be attached',
    'payment incomplete',
    'application incomplete',
    'Bank details incorrect',
    'Account does not exist',
    'Neft error'
]


def get_earning_message(self, app):
    client = app.client or app.quote.opportunity.lead
    return dict(
        collecting_application='We will reach out to you shortly to collect the application and cheque for your client %s' % client.contact.get_full_name(), # noqa
        collection_incomplete='We tried reaching out to you collect the application for your client, %s. However, we were not able to.\n\nYour partner success manager will reach out to you shortly.' % client.contact.get_full_name(), # noqa
        application_collected='The application and cheque for your client %s has been collected.' % (client.contact.get_full_name()), # noqa
        application_submitted='The application has been submitted to the insurer for the client %s' % (client.contact.get_full_name()), # noqa
        uw_pending='Your application for your client, %s has been put on hold by the under-writer. This happens because of either high age, abnormal BMI, high premium or past medical history.\n\nYour partner success manager will reach out to you shortly.' % client.contact.get_full_name(), # noqa
        medical_scheduled='The insurer has scheduled a medical checkup for the client, %s' % client.contact.get_full_name(), # noqa
        medical_completed='The insurer has completed the medical checkup for the client %s' % client.contact.get_full_name(), # noqa
        medical_incomplete='The medical checkup could not be completed for your client, %s\n\nYour partner success manager will reach out to you shortly.' % client.contact.get_full_name(), # noqa
        policy_issued='Policy %s for your client, %s has been issued.' % (app.policy.id, client.contact.get_full_name()), # noqa
        policy_rejected='Policy %s for your client, %s has been rejected.\n\nYour partner success manager will reach out to you shortly.' % (app.policy.id, client.contact.get_full_name()), # noqa
        policy_followup='Insurer has asked for additional documents for your application %s for your client, %s\n\nYour partner success manager will reach out to you shortly.' % (app.reference_no, client.contact.get_full_name()), # noqa
        application_resubmitted='The additional document that the insurer asked regarding your application %s for your client %s has been submitted.\n\nYour partner success manager will reach out to you shortly.' % (app.reference_no, client.contact.get_full_name()), # noqa
        loading_applied='Loading has been applied on your application %s for your client, %s. The same has been mailed to the customer.\n\nThe policy will move forward as soon as they have paid using the mail.\n\nYour partner success manager will reach out to you shortly.' % (app.reference_no, client.contact.get_full_name()), # noqa
        loading_paid='Loading has been paid on your application %s for your client, %s.' % (app.reference_no, client.contact.get_full_name()), # noqa
        commission_due='Congratulations. Commission has been paid on your application %s for your client %s' % (app.reference_no, client.contact.get_full_name()), # noqa
        commission_paid='Congratulations. Commission has been paid on your application # %s for your client %s' % (app.reference_no, client.contact.get_full_name()), # noqa
        commission_payment_error='There was an error processing your commission.\n\nYour partner success manager will reach out to your shortly.' # noqa
    ).get(self.status)
