"""Editable launch content. Prices are in paise; sources recorded in docs/pricing-research.md."""
SERVICES = [
    dict(slug='bath-brush', name='Bath & Brush', species='dog', price=71910, reference=79900, duration='45–90 minutes', eyebrow='WASH, DRY & BRUSH', description='A thorough wash, gentle dry, and coat-appropriate brush-out for everyday freshness.', includes=['Coat-appropriate shampoo & rinse','Gentle drying & brush-out','Nail clipping, when suitable','External ear cleaning'], image='hero.webp', featured=False),
    dict(slug='full-groom', name='The Full Groom', species='dog', price=107910, reference=119900, duration='60–120+ minutes', eyebrow='COMPLETE COAT CARE', description='Bathing and brushing, plus the haircut and finishing touches you agree with your groomer.', includes=['Everything in Bath & Brush','Agreed haircut & coat styling','Paw & hygiene trim','Personalized aftercare notes'], image='hero.webp', featured=True),
    dict(slug='cat-care', name='Gentle Cat Care', species='cat', price=103500, reference=115000, duration='Individual estimate', eyebrow='FOR OUR FELINE FRIENDS', description='A quieter approach, a familiar space, and care that follows their lead.', includes=['Cat-specific suitability check','Agreed brushing or coat care','Nail care, when suitable','Bathing only if appropriate'], image='cat.webp', featured=False),
    dict(slug='express-care', name='Express Care', species='both', price=None, reference=None, duration='Around 30 minutes if suitable', eyebrow='FOCUSED MAINTENANCE', description='Choose a nail trim, external ear clean, or brush-through between fuller grooming visits.', includes=['Choose the maintenance you need','Brush-through or nail care','Scope agreed before the visit','No bath or full haircut'], image='cat.webp', featured=False),
]

ARTICLES = [
 dict(slug='prepare-for-home-grooming',title='Their first home groom. Your easy checklist.',category='First-time pet parents',minutes=4,image='hero.webp',summary='A little preparation makes room for a calmer care day.',body='Choose a well-lit, ventilated space with room for the groomer and your pet. Before your visit, we will confirm whether water, electricity, a bathing area, and a clean personal towel are needed.\nTell the team about previous grooming experiences, handling preferences, and any veterinary instructions. Keep other pets in a separate comfortable space during setup.\nLet your pet meet the groomer without rushing. We review the agreed service and total quote together before work begins. Your groomer will explain where you can stay nearby.\nAfter the session, ask what was completed and what everyday coat care might help. Clinical questions and any unusual symptoms should go to your veterinarian.'),
 dict(slug='choose-a-grooming-package',title='Bath, brush, or the whole fluffy works?',category='Grooming basics',minutes=3,image='cat.webp',summary='Find a starting point that suits your pet, their coat, and your day.',body='Bath & Brush focuses on washing, drying, and brushing. Full Groom adds an agreed haircut or trim. Express Care is a smaller maintenance appointment and does not include a full bath or haircut.\nCoat condition, size, comfort, and handling requirements affect the time and quote. A breed name alone cannot tell the whole story. Share a description of your pet and discuss any concerns with the team.\nCats have a separate suitability conversation with a cat-experienced groomer. We do not simply apply a dog package to a cat.\nChoose a starting point online, then confirm the actual scope and complete price before the appointment. We never treat a timing estimate as a reason to rush a pet.'),
 dict(slug='care-between-visits',title='Small rituals. Happier coat days.',category='Everyday care',minutes=3,image='hero.webp',summary='Simple questions to ask your groomer about care between appointments.',body='Ask your groomer which brush is appropriate for your pet and how to use it gently. A short, comfortable routine can be easier to maintain than a long session.\nAvoid forcing handling when your pet is uncomfortable. Share what they enjoy and what they find difficult before the next appointment.\nKeep a note of your previous service, products used, and any instructions supplied by your veterinarian. If a skin or ear concern appears, ask your veterinarian rather than attempting treatment through grooming.\nGrooming frequency varies with coat, lifestyle, and individual needs. Plan the next visit through a conversation instead of following a universal calendar.'),
]

SIZE_GUIDES = {
 'dog': [
   dict(value='small',label='Small (Chihuahua, Shih Tzu, Pug)'),
   dict(value='medium',label='Medium (Beagle, Cocker Spaniel, Border Collie)'),
   dict(value='large',label='Large (Labrador, Golden Retriever, German Shepherd)'),
   dict(value='giant',label='Giant (Great Dane, Saint Bernard, Mastiff)'),
 ],
 'cat': [
   dict(value='small',label='Small (Singapura, Cornish Rex)'),
   dict(value='medium',label='Medium (Siamese, Persian, Domestic Shorthair)'),
   dict(value='large',label='Large (Maine Coon, Ragdoll, Norwegian Forest Cat)'),
 ],
}

# Update only untouched starter copy in existing databases. Owner edits are preserved.
COPY_BASELINES = {
 'services': {
   'bath-brush': dict(description='A fresh coat, softer cuddles, and a little more spring in their step.',eyebrow='THE EVERYDAY REFRESH'),
   'full-groom': dict(description='From fluffy beginnings to a beautifully groomed finish. All in their happy place.',eyebrow='A LITTLE EXTRA TLC'),
   'express-care': dict(description='A focused nail, external ear, or coat tidy-up. A little care goes a long way.',eyebrow='BETWEEN THE BIG GROOMS'),
 },
 'articles': {
   'prepare-for-home-grooming': dict(title='Their first home groom. Your easy checklist.',summary='A little preparation makes room for a calmer care day.'),
   'choose-a-grooming-package': dict(title='Bath, brush, or the whole fluffy works?',summary='Find a starting point that suits your pet, their coat, and your day.'),
   'care-between-visits': dict(title='Small rituals. Happier coat days.',summary='Simple questions to ask your groomer about care between appointments.'),
 },
}

# Refined titles retain their URLs and any separately edited article body.
for article, title, summary in zip(ARTICLES, [
 'Getting your home ready for a grooming visit',
 'Bath & Brush or Full Groom: which does your pet need?',
 'Between appointments: a practical coat-care routine',
], [
 'Space, towels, access, and what to tell the groomer before they arrive.',
 'Compare inclusions, timing, and the questions that help you choose.',
 'Build a manageable routine around your pet’s coat and preferences.',
]):
    article.update(title=title,summary=summary)

# Migrate the untouched starter body while preserving any owner-written version.
COPY_BASELINES['articles']['prepare-for-home-grooming']['body'] = ARTICLES[0]['body']
ARTICLES[0]['body'] = (
 '## Before your groomer arrives\n'
 'Your Tailvic groomer comes to your home. Choose a well-lit, ventilated area where they can work comfortably with your pet. Our team will confirm whether your chosen service needs access to water, electricity, a bathing area, and a clean towel before the groomer arrives.\n'
 '## Tell us about your pet\n'
 'Share previous grooming experiences, handling preferences, sensitivities, and any instructions from your veterinarian when you request the appointment. Confirm the service, estimated duration, complete quote, and home address with the team.\n'
 '## Make room for a calm introduction\n'
 'Keep other pets in a separate comfortable space while the groomer brings in their equipment. Let your pet meet the groomer at their own pace. The groomer will review the agreed work and explain where you can stay nearby.\n'
 '## During the home appointment\n'
 'Ask about the tools and products before grooming begins. Share what helps your pet settle and let the groomer know if your pet needs a break. Any change to the agreed service should be discussed with you first.\n'
 '## Before the groomer leaves\n'
 'Review what was completed, ask for everyday coat-care notes, and check that the grooming area has been tidied. You can discuss the next home appointment with the team. Clinical questions or unusual symptoms should go to your veterinarian.'
)

ARTICLES.extend([
 dict(slug='choosing-a-dog-brush',title='Which brush suits your dog’s coat?',category='Tools & techniques',minutes=4,image='hero.webp',summary='Bristles, pins, and grooming mitts: understand the options before buying.',sources=[dict(title='American Kennel Club: choosing a dog brush',url='https://www.akc.org/expert-advice/health/types-dog-brushes-shedding/')],body='## Start with the coat, not the packaging\nThe right tool depends on coat texture and length. Bristle brushes and rubber grooming mitts can suit shorter coats; pin brushes are often used on longer coats. A slicker has a different purpose and needs a gentle technique. Ask a groomer to demonstrate on your individual dog.\n## Check the tool together\nBring your current brush to the next appointment. Ask whether the pins, spacing, and firmness suit the coat, and which areas need a different approach. A tool that works for another dog may not be right for yours.\n## Keep comfort in view\nUse light pressure and stop if brushing catches or your dog becomes uncomfortable. Do not turn a stubborn tangle into a pulling contest. Ask for help with knots that will not release gently.\n## Before you buy\nWrite down the recommended brush type and ask how it should be cleaned. Buy for the job you actually need to do rather than assembling a large kit.\n## Make the next visit useful\nWhen you book with Tailvic, mention your coat-care questions in the notes. Ask the groomer to show the technique before the visit ends, then agree a routine you can realistically maintain.'),
 dict(slug='introducing-your-cat-to-grooming',title='Helping your cat get comfortable with brushing',category='Cat care',minutes=4,image='cat.webp',summary='A quieter introduction, short sessions, and permission to take a break.',sources=[dict(title='Cats Protection: grooming your cat',url='https://www.cats.org.uk/help-and-advice/cat-behaviour/grooming'),dict(title='Battersea: cat grooming',url='https://www.battersea.org.uk/pet-advice/cat-advice/cat-grooming')],body='## Pick a calm moment\nChoose a familiar, quiet place when your cat is relaxed. Keep the introduction brief and give them room to leave. Let them investigate the brush before trying a few gentle strokes in an area they already accept being touched.\n## Build up slowly\nShort sessions with praise can help brushing become familiar. End before your cat becomes upset. The aim is a comfortable routine, not finishing the whole coat at once.\n## Listen to their response\nPause if your cat moves away or objects. Avoid holding them down to finish a session. If tangles are difficult to manage, discuss professional help instead of forcing them out.\n## Share their preferences\nBefore a home appointment, tell the team about past grooming, handling dislikes, and any veterinary instructions. Ask which services are suitable and whether a cat-experienced groomer is available.\n## Set up for the visit\nTailvic confirms preparation needs with you. Keep other pets away from the working area and agree where you will stay nearby. Bathing is discussed individually and is not automatically part of every cat appointment.\n## When the question belongs with a vet\nChanges in grooming habits or concerns about skin and coat should be discussed with your veterinarian. A grooming appointment does not replace clinical assessment.'),
])

BREEDS = [
 ('labrador','Labrador','Short coat, plenty of personality. Discuss brushing, bathing, and seasonal shedding.'),
 ('golden-retriever','Golden Retriever','A beautiful longer coat. Plan brush-outs and individual coat maintenance.'),
 ('german-shepherd','German Shepherd','Double-coat care starts with the right tools and a patient approach.'),
 ('shih-tzu','Shih Tzu','Choose a comfortable style and plan the upkeep that goes with it.'),
 ('pug','Pug','Short-coat care with attention to individual comfort and handling.'),
 ('persian-cat','Persian Cat','Long-coat care with a cat-experienced professional and a suitability conversation.'),
 ('indie-dog','Indie dogs','Every coat is different. Choose care around your individual companion.'),
]

FAQS = [
 ('Where do you groom?','At-home grooming is currently available in Gurugram Sectors 69, 70 and 71. Message the team with your address to check coverage. Travel and applicable taxes are confirmed before an appointment is agreed.'),
 ('Does grooming take just 30 minutes?','Around 30 minutes is a target for suitable express maintenance. Baths, full haircuts, deshedding, and some cat appointments take longer. Your pet’s comfort comes first; we confirm an individual estimate.'),
 ('How do I ask about a grooming visit?','Message or call the Tailvic team to share your pet’s needs and preferred timing. A visit is agreed directly with the team; online booking and live availability are not currently offered.'),
 ('Are travel and taxes included?','Displayed prices are service estimates and exclude travel and applicable taxes. We send a complete quote before confirmation. Payment is available only after that quote is approved.'),
 ('What should I have ready?','A safe, well-lit grooming area, access to water and electricity where needed, a bathing area, and a clean towel. We confirm the service-specific checklist before visiting.'),
 ('What if my pet is nervous?','Tell us before the appointment. We plan handling around your pet and pause or stop if continuing is unsuitable. No appointment time target overrides comfort.'),
 ('Do you offer vaccination?','Vaccination administration and veterinary consultations are planned services. Current wellness enquiries cover information and interest in reminders based on your veterinarian’s schedule.'),
 ('How does UPI payment work?','After the team supplies a complete quote, you can open your UPI app or scan a QR code. Submit the transaction reference afterward. Payment remains awaiting verification until Tailvic checks receipt.'),
]

POLICIES = {
 'privacy': ('Privacy & your information','We collect the contact, address, pet, and appointment details needed to arrange care. Account passwords are hashed and are not stored as readable text. We use first-party analytics only after your choice, and do not put names, phone numbers, or health notes into analytics.\nOptional reminder and marketing choices are separate from booking. Contact tailvic@gmail.com to request access, corrections, or deletion of your information. Booking records may need to be retained for legitimate operational obligations.\nUPI payments take place through your UPI provider. Tailvic stores the amount and reference you submit, not your UPI PIN or banking credentials. External WhatsApp and Instagram links follow their own privacy practices.'),
 'terms': ('Care, with clear expectations','Appointments are subject to coverage, groomer suitability, and the complete agreed quote. Contact Tailvic to discuss a preferred time; the team confirms whether a visit can be arranged.\nPrices shown exclude travel and applicable taxes. No additional work begins without agreement. Our approximately 30-minute express target is an estimate for suitable maintenance services, not a promise for full grooming.\nCustomers should share relevant handling preferences, health restrictions, and veterinary instructions. Grooming is not veterinary diagnosis or treatment. We pause or stop when continuing is unsuitable.'),
 'cancellations-and-refunds': ('When plans change','Please contact +91 74857 84578 as soon as you need to change your appointment. Our launch policy allows cancellation before the visit without a cancellation fee. Contact the team to arrange a new time.\nIf Tailvic cancels, we will offer a new appointment or refund any verified payment for unprovided services. If a visit stops early, we explain what was completed and agree the applicable charge with you.\nReport a service concern with your booking reference. We assess an appropriate remedy, which may include suitable rework or a refund. Refunds require payment verification and are processed manually; the team confirms timing and reference.'),
 'accessibility': ('Care should be easy to reach','We aim for readable text, keyboard navigation, visible focus, and accessible booking controls across screen sizes. If something prevents you from using the website, call +91 74857 84578 or email tailvic@gmail.com. Our team can help arrange an appointment by phone.'),
}

POLICIES['privacy']=(POLICIES['privacy'][0],POLICIES['privacy'][1]+'\nGroomer applicants can share contact details, location, professional experience, qualifications, an optional CV or portfolio link, and an introduction. These are stored privately for the Tailvic owner to review and contact the applicant about recruitment. They are not displayed in public profiles or used as customer testimonials. Contact tailvic@gmail.com to correct or request deletion of an application, quoting its reference. Do not submit identity documents or bank details through the careers form.')
