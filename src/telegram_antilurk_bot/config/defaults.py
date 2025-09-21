"""Default puzzles for the bot."""

from .schemas import Puzzle


def get_default_puzzles() -> list[Puzzle]:
    """Generate 100 Mind of Steele-themed multiple-choice puzzles."""
    puzzles: list[Puzzle] = []

    # Add some basic arithmetic puzzles first
    arithmetic_data = [
        ("What is 7 + 8?", ["15", "14", "16", "13"]),
        ("What is 12 × 3?", ["36", "35", "39", "33"]),
        ("What is 45 ÷ 9?", ["5", "4", "6", "7"]),
        ("What is 23 - 8?", ["15", "14", "16", "17"]),
        ("What is 6 × 7?", ["42", "41", "43", "40"]),
        ("What is 81 ÷ 9?", ["9", "8", "10", "7"]),
        ("What is 15 + 27?", ["42", "41", "43", "40"]),
        ("What is 64 ÷ 8?", ["8", "7", "9", "6"]),
        ("What is 9 × 4?", ["36", "35", "37", "34"]),
        ("What is 56 - 19?", ["37", "36", "38", "35"]),
        ("What is 13 + 29?", ["42", "41", "43", "40"]),
        ("What is 72 ÷ 6?", ["12", "11", "13", "10"]),
        ("What is 8 × 9?", ["72", "71", "73", "70"]),
        ("What is 91 - 28?", ["63", "62", "64", "61"]),
        ("What is 25 + 17?", ["42", "41", "43", "40"]),
        ("What is 54 ÷ 6?", ["9", "8", "10", "7"]),
        ("What is 7 × 8?", ["56", "55", "57", "54"]),
        ("What is 83 - 26?", ["57", "56", "58", "55"]),
        ("What is 19 + 24?", ["43", "42", "44", "41"]),
        ("What is 48 ÷ 8?", ["6", "5", "7", "4"]),
        ("What is 11 × 6?", ["66", "65", "67", "64"]),
        ("What is 75 - 31?", ["44", "43", "45", "42"]),
        ("What is 16 + 35?", ["51", "50", "52", "49"]),
        ("What is 63 ÷ 7?", ["9", "8", "10", "7"]),
        ("What is 5 × 12?", ["60", "59", "61", "58"]),
    ]

    for i, (question, choices) in enumerate(arithmetic_data):
        puzzles.append(
            Puzzle(
                id=f"arith_{i + 1:03d}",
                type="arithmetic",
                question=question,
                choices=choices,  # First choice is correct
            )
        )

    # All puzzles below are derived from themes, quotes, and satire found in the
    # Mind of Steele scripts under scripts/mind_of_steele_*.md (chemtrails/fog,
    # sovereign citizens, Vobesology, TPR/Banaman, fuel-catalyst grifts, etc.).
    data = [
        (
            "Which 'trust' did Richard Vobes claim could pay a water bill?",
            [
                "Cestui Que Vie trust",
                "Santa's Gift Fund",
                "Enid Blyton Trust",
                "Otter Conservation Fund",
            ],
            0,
        ),
        (
            "What does Sovereign Pete claim DVLA 'registration' does to your car?",
            [
                "Transfers ownership to the state",
                "Doubles horsepower",
                "Makes it amphibious",
                "Erases speeding points",
            ],
            0,
        ),
        (
            "Why do conspiracy theorists think you can pay bills with a signature?",
            [
                "They believe 'acceptance for value' taps a secret trust",
                "A wet-ink signature instructs banks to transfer funds",
                "Using blue ink nullifies debts",
                "Paper naturally absorbs taxes on contact",
            ],
            0,
        ),
        (
            "Banaman puzzled over a crest on which document in the Liverpool saga?",
            ["A warrant", "A bus ticket", "A TV licence", "A library card"],
            0,
        ),
        (
            "Which group appears alongside Banaman in the Liverpool court caper?",
            [
                "TPR (Liverpool People's Resistance)",
                "Mensa Liverpool",
                "Knights of Columbus",
                "Rotary Club of Crosby",
            ],
            0,
        ),
        (
            "In the Banaman/Liverpool TPR court video, which 'doctrine' was mis-invoked to justify 'home defense'?",
            ["Castle Doctrine", "Doctrine of Discovery", "Monroe Doctrine", "Shock Doctrine"],
            0,
        ),
        (
            "Which complaint do sovereign citizens often make about ALL CAPS names?",
            [
                "It's 'Dog Latin' with no standing",
                "It's Morse code for taxes",
                "It's a naval distress flag",
                "It's an anagram for 'Crown'",
            ],
            0,
        ),
        (
            "Fuel 'catalyst' grifters on Vobes's show claimed pellets worked in what?",
            [
                "Any engine: cars, bikes, even lawnmowers",
                "Only vintage carburetted cars",
                "Only diesel trucks over 3.5t",
                "Only hybrid vehicles",
            ],
            0,
        ),
        (
            "Why do 'fuel-catalyst' claims about a galvanic reaction in petrol fail?",
            [
                "Petrol is an electrical insulator",
                "Diesel freezes at room temp",
                "Oxygen is a noble gas",
                "Water burns in engines",
            ],
            0,
        ),
        (
            "Which trope explains why miracle devices 'never catch on'?",
            [
                "Grand suppression narrative",
                "Patent office backlog",
                "Quantum misalignment",
                "Astrological embargo",
            ],
            0,
        ),
        (
            "Chemtrail believers misread which ordinary phenomenon?",
            [
                "Persistent contrails from jet exhaust",
                "Sun dogs at low angles",
                "Noctilucent clouds only at poles",
                "Sprites above thunderstorms",
            ],
            0,
        ),
        (
            "Who claimed nicotine isn't addictive?",
            ["Bryan Ardis", "Andrew Wakefield", "David Icke", "Sasha Stone"],
            0,
        ),
        (
            "Rachel Matthews's 'experiment' involved what, to Vobes's delight?",
            [
                "Trying pipe tobacco",
                "Measuring chemtrails",
                "Building a Faraday cage",
                "Counting pyramids",
            ],
            0,
        ),
        (
            "Which bogus fix did Vobes platform to 'save fuel'?",
            [
                "Drop-in tank pellets",
                "Aluminium foil on bonnet",
                "Stronger spark plugs only",
                "Inflatable spoiler",
            ],
            0,
        ),
        (
            "What UK agency is cast as a 'corporation' that 'owns your car' if you register it?",
            ["DVLA", "HMRC", "Ofcom", "NATS"],
            0,
        ),
        (
            "Which set phrase is mocked as a magic debt-eraser?",
            [
                "Acceptance for Value",
                "In Perpetuity Forever",
                "Force Majeure Me",
                "Without Prejudice Pay",
            ],
            0,
        ),
        (
            "What do sovereign-citizen influencers claim the term 'license' means?",
            [
                "Asking permission to use 'their' property",
                "Secret Crown lien",
                "Immunity from traffic laws",
                "Automatic diplomatic status",
            ],
            0,
        ),
        (
            "Which scientific point dismantles 'fog full of nanobots' claims?",
            [
                "Weather and illness co-occur without causation",
                "Fog is dry ice residue",
                "Nanobots need 5G to swim",
                "Humidity kills viruses instantly",
            ],
            0,
        ),
        (
            "What implausible authority did a TPR spokesman cite for global crimes?",
            [
                "Canada's Defence Minister",
                "Interpol's Pope",
                "UN Sheriff of Health",
                "MI5 Chief Pharmacist",
            ],
            0,
        ),
        (
            "What courtroom step did Michael (with Liverpool TPR) claim he could refuse?",
            [
                "Entering a plea for the 'legal fiction'",
                "Sitting in the dock",
                "Standing for the judge",
                "Swearing on any book",
            ],
            0,
        ),
        (
            "Which phrase do sovereigns misuse to claim 'government has no authority'?",
            [
                "Clearfield Doctrine",
                "Section 31 Immunity",
                "Rule in Shelley's Case",
                "Nemo Dat Doctrine",
            ],
            0,
        ),
        (
            "Which claim about 5G streetlights do conspiracy influencers promote?",
            [
                "They are secret energy weapons",
                "They harvest rainwater",
                "They detect flat tyres",
                "They contain petrol",
            ],
            0,
        ),
        (
            "What body part did a protester say 5G uniquely harms tenfold?",
            ["Ovaries", "Appendix", "Eyelashes", "Kneecaps"],
            0,
        ),
        (
            "Which brain area was bizarrely blamed on 5G damage?",
            ["Amygdala", "Pons", "Occipital lobe", "Cerebellar vermis"],
            0,
        ),
        (
            "When protest videos show a handheld meter 'off the scale' near 5G masts, what does that actually indicate?",
            [
                "Nothing scientific about 5G risk",
                "Guaranteed lethal rays",
                "Quantum weather hacks",
                "Ion engines in lampposts",
            ],
            0,
        ),
        (
            "What mythical paperwork status do sovereigns seek for jurors?",
            [
                "'Sovereign men' not on electoral roll",
                "All jurors must be tradesmen",
                "Jury of internet subscribers",
                "Only unlicensed drivers allowed",
            ],
            0,
        ),
        (
            "What everyday thing did Vobes compare to 'financial noclip mode'?",
            [
                "Signing bills to 'pay' them",
                "Using contactless twice",
                "Refunding a refund",
                "Tapping a lamppost",
            ],
            0,
        ),
        (
            "Which literary figure is used to frame 'escape from responsibility'?",
            ["Reginald Perrin", "Jay Gatsby", "Holden Caulfield", "Bertie Wooster"],
            0,
        ),
        (
            "What do some conspiracy influencers claim a warrant must bear to be 'valid'?",
            [
                "An original wet-ink signature",
                "A proclamation of common law",
                "A gold seal proving nobility",
                "A chemtrail-resistant watermark",
            ],
            0,
        ),
        (
            "Which profession did Banaman repeatedly confuse in his videos?",
            ["Basic legal procedure", "Basic plumbing", "Basic cartography", "Basic bee keeping"],
            0,
        ),
        (
            "What's the punchline about 'sovereign' status, as claimed by sovereign citizens?",
            [
                "A sovereign cannot be subject—so they invent loopholes",
                "Sovereigns get free petrol",
                "Sovereigns outrank traffic lights",
                "Sovereigns vote twice",
            ],
            0,
        ),
        (
            "What sky claim does Ian Livingstone make?",
            [
                "He can spot 'real' vs 'fake' clouds",
                "He owns a private weather map",
                "He pilots anti-cloud drones",
                "He times rainbow durations",
            ],
            0,
        ),
        (
            "Which absurd machine is invoked to 'manufacture clouds'?",
            [
                "A mainframe with an antenna",
                "A lawnmower on a kite",
                "A copper pyramid engine",
                "An inflatable Tesla coil",
            ],
            0,
        ),
        (
            "If a 'mainframe' makes clouds, what happens to chemtrails logic?",
            [
                "It contradicts itself",
                "It becomes proven",
                "It needs bigger planes",
                "It requires 6G",
            ],
            0,
        ),
        (
            "What basic property of petrol prevents any 'galvanic reaction' in a fuel tank?",
            [
                "No ions: current can't flow",
                "Wrong pH for sparks",
                "Too cold to oxidize",
                "Too viscous for voltage",
            ],
            0,
        ),
        (
            "Which sales tactic do grifters use on Vobes's channel?",
            [
                "Anonymous testimonials and vague tech",
                "ISO lab certification",
                "Peer-reviewed trials",
                "Refund guarantees honored",
            ],
            0,
        ),
        (
            "What role does Richard Vobes effectively play for product scammers?",
            [
                "Their marketing department",
                "Their compliance auditor",
                "Their chief engineer",
                "Their legal counsel",
            ],
            0,
        ),
        (
            "What everyday agency do sovereigns insist is purely 'corporate'?",
            [
                "United Kingdom via DVLA",
                "NHS surgical wards",
                "BBC local radio",
                "National Trust properties",
            ],
            0,
        ),
        (
            "What do sovereign-citizen influencers claim about UK driving test pass rates?",
            [
                "Only 49% can ever pass by design",
                "You pass automatically at 30",
                "Manual cars get bonus points",
                "Sunroof owners always fail",
            ],
            0,
        ),
        (
            "What do some sovereign-citizen influencers claim is a 'test' of male authority at dinner?",
            [
                "Stopping a partner from taking a chip",
                "Choosing the restaurant proves leadership",
                "Passing the salt establishes dominance",
                "Forks must display a royal crest",
            ],
            0,
        ),
        (
            "What mythical emergency power does a 'registered keeper' grant police?",
            [
                "Kick your door in without warrant",
                "Seize your goldfish",
                "Rewrite your MOT",
                "Downgrade your license",
            ],
            0,
        ),
        (
            "Which fictional 'code' do sovereigns claim governs roads?",
            [
                "Corporate Highway Code contract",
                "Pirate Admiralty Roadbook",
                "Royal Coachman's Ledger",
                "Motor Magna Carta",
            ],
            0,
        ),
        (
            "Why are 'fuel conspiracies' attractive to guests on Richard Vobes's channel?",
            [
                "They sell easy, magical fixes",
                "They require lab skill",
                "They need patents first",
                "They reduce emissions reliably",
            ],
            0,
        ),
        (
            "What mundane explanation beats 'chemtrail' timing coincidences?",
            [
                "Weather + illness co-occur often",
                "Moon phase dictates trails",
                "Pilot's mood affects clouds",
                "Airport lunch menu changes",
            ],
            0,
        ),
        (
            "Sovereign paperwork often seeks what escape?",
            [
                "Freedom from consequences",
                "Extra voting rights",
                "Secret tax refunds",
                "Airport lounge access",
            ],
            0,
        ),
        (
            "What should skeptics do when hearing grand claims from conspiracy influencers?",
            [
                "Skepticism should also question grifters",
                "Questioning equals truth",
                "Belief beats data",
                "Intuition trumps physics",
            ],
            0,
        ),
        (
            "The 'Crown has no standing' rant bundled what?",
            [
                "A grab-bag of misused international laws",
                "Precise case law citations",
                "Accurate treaty summaries",
                "Verified lab results",
            ],
            0,
        ),
        (
            "What do UK conspiracy activists often claim about recent persistent fog?",
            [
                "It contains harmful chemicals or 'nanobots'",
                "It's cold soot from vintage planes",
                "It's harmless water droplets",
                "It's invisible 7G foam",
            ],
            0,
        ),
        (
            "Why do 'suppressed truth' myths persist among conspiracy promoters?",
            [
                "They flatter believers as heroes",
                "They demand hard work",
                "They punish lying",
                "They hate attention",
            ],
            0,
        ),
        (
            "What 'legal fiction' trick did Michael's group attempt?",
            [
                "Power of attorney games",
                "Embassy-as-home claim",
                "Common law ID badge",
                "Sovereign postage stamp",
            ],
            0,
        ),
        (
            "In the fog panic, what measurement was requested?",
            [
                "Use a voltmeter on the fog",
                "Send a stool sample",
                "Weigh a cloud at noon",
                "Time raindrop speed",
            ],
            0,
        ),
        (
            "What do product promoters on conspiracy shows often do during interviews?",
            [
                "Flog unproven products to the audience",
                "Provide balanced technical briefings",
                "Discourage purchases as unsafe",
                "Offer free MOT vouchers",
            ],
            0,
        ),
        (
            "Which UK town area featured in 5G panic meters?",
            ["Crosby", "Swindon", "Truro", "Grantham"],
            0,
        ),
        (
            "What everyday physics explains contrails lingering?",
            [
                "Humidity/temperature at altitude",
                "Magnetic north drift",
                "Solar wind pressure",
                "Cosmic ray showers",
            ],
            0,
        ),
        (
            "What does 'acceptance for value' promise believers?",
            [
                "Debt erasure by signature",
                "Cheaper mortgages",
                "Free road tax",
                "Unlimited childcare",
            ],
            0,
        ),
        (
            "Which character archetype do scammers assume on Vobes's show?",
            [
                "Tortured, suppressed prophet",
                "Reluctant billionaire",
                "Accidental genius chef",
                "Undercover meteorologist",
            ],
            0,
        ),
        (
            "The 'lawnmower test' mocked what claim?",
            [
                "Universal fuel gadget works anywhere",
                "Grass blocks airflow",
                "Two-stroke engines can't idle",
                "Electric mowers drink petrol",
            ],
            0,
        ),
        (
            "When jurors are on the electoral roll, the sovereign says what?",
            [
                "They're 'subjects', not peers",
                "They are 'aliens' in law",
                "They owe maritime fees",
                "They must wear caps",
            ],
            0,
        ),
        (
            "What do sovereign citizens claim about the ALL CAPS 'strawman' vs the living person?",
            [
                "ALL CAPS is a separate corporate entity",
                "Itals indicate maritime law applies",
                "Emojis indicate consent to contract",
                "Invisible ink proves sovereignty",
            ],
            0,
        ),
        (
            "What pattern is seen among product‑promoting guests on Richard Vobes's channel?",
            [
                "Charlatans flogging products",
                "Qualified experts only",
                "Neutral historians",
                "Meteorologists debating weather",
            ],
            0,
        ),
        (
            "A 'crest' on paperwork caused what reaction?",
            [
                "Confusion marketed as mystery",
                "Instant compliance",
                "Blank acceptance",
                "Shredding on sight",
            ],
            0,
        ),
        (
            "What supposed 'digital product' did Vobes scorn compared to tobacco?",
            ["Vapes", "Nicotine gum", "Air purifiers", "Smart kettles"],
            0,
        ),
        (
            "The show's chemistry point about fuels emphasizes what?",
            [
                "Refined hydrocarbons lack free ions",
                "Diesel dissolves magnets",
                "Octane resists gravity",
                "Petrol emits cold heat",
            ],
            0,
        ),
        (
            "Which line best sums up sovereign-citizen logic?",
            [
                "Invent loopholes to dodge reality",
                "Respect law to fix policy",
                "Use courts to clarify science",
                "Balance rights with duties",
            ],
            0,
        ),
        (
            "Which UK doc is joked about as needing 'wet ink'?",
            [
                "Any 'warrant' they don't like",
                "Supermarket receipt",
                "Passport photo page",
                "Cinema ticket",
            ],
            0,
        ),
        (
            "In spoof legalisms, what is 'spelling'?",
            [
                "'Witchcraft' that binds you",
                "A maritime tax trap",
                "A VAT for letters",
                "A railway bylaw",
            ],
            0,
        ),
        (
            "What do sovereign-citizen narratives implicitly promise followers?",
            [
                "Escapism from consequences",
                "Expertise in explosives",
                "Soap-making metaphors",
                "Basement leases",
            ],
            0,
        ),
        (
            "What cure-all status did Ardis ascribe to nicotine?",
            [
                "Preventative/curative for Alzheimer's",
                "Antibiotic for colds",
                "Antidote to chemtrails",
                "Vaccine booster",
            ],
            0,
        ),
        (
            "Why are 'suppressed devices' stories convenient?",
            [
                "They justify selling unproven junk",
                "They demand peer review first",
                "They forbid online sales",
                "They cap profits",
            ],
            0,
        ),
        (
            "What do believers forget about illness spikes and weather?",
            [
                "Correlation isn't causation",
                "Colds require 5G",
                "Fog produces viruses",
                "Rain sterilizes cities",
            ],
            0,
        ),
        (
            "What do scam product demonstrations frequently avoid?",
            [
                "Transparent methodology and data",
                "Friendly audiences",
                "Dramatic music cues",
                "PowerPoint slides",
            ],
            0,
        ),
        (
            "What common prop appears in 'meter panic' videos?",
            ["A beeping handheld RF meter", "A Bunsen burner", "A stethoscope", "A sextant"],
            0,
        ),
        (
            "What do sovereigns call the person-state mismatch?",
            [
                "Strawman in ALL CAPS",
                "Ghost debtor in italics",
                "Maritime echo in brackets",
                "Shadow ID in bold",
            ],
            0,
        ),
        (
            "What emotions do grifters commonly exploit?",
            ["Fear and grievance", "Professional pride", "Math anxiety", "Love of Latin"],
            0,
        ),
        (
            "Which absurd residency claim shows up in protests?",
            [
                "'Embassy' houses immune to law",
                "'Cloud nation' passports",
                "'Sovereign tents' on roads",
                "'Sea lane' driveways",
            ],
            0,
        ),
        (
            "What do contrails primarily consist of?",
            ["Water vapor/ice crystals", "Liquid mercury", "Graphene flakes", "Boron dust"],
            0,
        ),
        (
            "Why is 'unlimited debt-clearing' so tempting in the story?",
            [
                "It promises reward without effort",
                "It needs training",
                "It builds community",
                "It funds schools",
            ],
            0,
        ),
        (
            "What lighthearted animal is contrasted with extremists?",
            ["Otter", "Badger", "Hedgehog", "Puffin"],
            0,
        ),
        (
            "When RF meters 'go off the scale' in protest videos, what does that often signal?",
            [
                "User error or misuse",
                "Nuclear fallout",
                "Tesla coils nearby",
                "X-ray beams in lampposts",
            ],
            0,
        ),
        (
            "What UK paperwork do sovereigns demand to see on the spot?",
            [
                "Original wet-ink warrant",
                "MP's voting record",
                "Council's Wi-Fi password",
                "Judge's private notes",
            ],
            0,
        ),
        (
            "Why is 'jury of sovereigns only' impossible?",
            [
                "It defies basic civic rules",
                "It requires DNA tests",
                "It needs royal assent",
                "It must be televised",
            ],
            0,
        ),
        (
            "What product type is a red flag on Vobes's show?",
            [
                "Universal miracle fix",
                "Open-source software",
                "Workshop manuals",
                "Tyre pressure gauges",
            ],
            0,
        ),
        (
            "Banaman's videos often begin with what?",
            [
                "Confusion about the obvious",
                "A legal citation spree",
                "Drone establishing shots",
                "A weather report",
            ],
            0,
        ),
        (
            "How do conspiracy promoters often react when basic science contradicts them?",
            [
                "Dismiss it as part of the cover‑up",
                "Submit to peer review",
                "Immediately retract the claim",
                "Report themselves to trading standards",
            ],
            0,
        ),
        (
            "Which phrase best captures the flaw in sovereign-citizen thinking about reality?",
            [
                "You can't loophole reality",
                "Paper beats physics",
                "Ink outruns gravity",
                "Caps lock trumps law",
            ],
            0,
        ),
        (
            "What do 'sovereign' court antics usually produce?",
            [
                "Self-sabotage and delays",
                "Instant acquittal",
                "Case dismissal with apology",
                "Jury standing ovations",
            ],
            0,
        ),
        (
            "Which device port did a scam claim to use?",
            ["OBD diagnostic port", "HDMI port", "USB-C on the dash", "SIM tray under seat"],
            0,
        ),
        (
            "Why do persistent contrails vary so much?",
            [
                "Atmospheric conditions differ",
                "Plane brand logos differ",
                "Pilot birthdays differ",
                "Fuel octane birthdays",
            ],
            0,
        ),
        (
            "What kind of 'proof' do chemtrailers offer most?",
            [
                "Anecdotes and vibes",
                "Weather station logs",
                "Satellite humidity maps",
                "Peer-reviewed aerosol spectra",
            ],
            0,
        ),
        (
            "Why are 'mainframe weather beams' mocked?",
            [
                "No mechanism or evidence",
                "They aim too high",
                "They cost £12.50",
                "They need moonlight",
            ],
            0,
        ),
        (
            "What rhetorical move frames grifters as martyrs?",
            [
                "Cassandra/Galileo comparison",
                "Robin Hood swagger",
                "Sherlock deduction",
                "Bond villain monologue",
            ],
            0,
        ),
        (
            "Which document did Vobes 'accept for value'?",
            ["A water bill", "A TV license renewal", "A parking ticket", "A train timetable"],
            0,
        ),
        (
            "What 'department' supposedly issues the property you drive?",
            [
                "Transport via DVLA",
                "Housing via HM Land Reg",
                "Defence via MOD",
                "Culture via DCMS",
            ],
            0,
        ),
        (
            "The show's view of 'question everything' is what?",
            [
                "Question grifters hardest",
                "Question only the state",
                "Question clouds exclusively",
                "Question never—just feel",
            ],
            0,
        ),
        (
            "Why do chemtrail narratives appeal to believers?",
            [
                "They explain any weather as deliberate action",
                "They limit claims to rare events",
                "They are falsified by every cloud",
                "They require no airplanes",
            ],
            0,
        ),
        (
            "What petty 'test' of respect do some influencers promote at dinner?",
            [
                "Stealing a chip at dinner",
                "Holding the TV remote",
                "Parking left of bins",
                "Counting teaspoons",
            ],
            0,
        ),
        (
            "Why do 'magic signatures' fail in reality?",
            [
                "Contracts and debts require payment",
                "Pens lack legal ink",
                "Paper is maritime-only",
                "Numbers outrank names",
            ],
            0,
        ),
        (
            "Why do simple miracle products appeal to conspiracy audiences?",
            [
                "Simple stories beat complex truths",
                "Labs are too noisy",
                "Pilots fly too low",
                "Meters beep too softly",
            ],
            0,
        ),
        (
            "What's the comedic fate of many Vobes-endorsed gadgets?",
            [
                "No evidence, then silence",
                "Immediate regulation",
                "Open-source replication",
                "University adoption",
            ],
            0,
        ),
        (
            "What courtroom buzzword do sovereigns misuse most?",
            ["Standing", "Res judicata", "Mens rea", "Quantum meruit"],
            0,
        ),
        (
            "Which city is a recurring backdrop for TPR drama?",
            ["Liverpool", "Bath", "York", "Norwich"],
            0,
        ),
        (
            "What do TPR supporters claim about the Crown's 'standing'?",
            [
                "They allege the Crown has no standing",
                "They allege the Crown owns all juries",
                "They allege the Crown is a charity",
                "They allege the Crown flies the planes",
            ],
            0,
        ),
        (
            "Sovereigns claim jurors on the roll are what?",
            [
                "State-owned 'enterprises'",
                "Royal witnesses",
                "Privateers at sea",
                "Unlettered clerks",
            ],
            0,
        ),
        (
            "Why doesn't 'OBD miracle dongle' save petrol?",
            [
                "It can't change combustion chemistry",
                "OBD only powers USB",
                "It drains windshield fluid",
                "It reroutes exhaust",
            ],
            0,
        ),
        (
            "What should you demand from grand claims by conspiracy promoters?",
            [
                "Demand mechanisms and data",
                "Cheer first, test later",
                "Buy now, think later",
                "Accept if suppressed",
            ],
            0,
        ),
        (
            "Which 'movement' recurs as a punchline?",
            ["Sovereign citizen", "Minimalist cooking", "Amateur radio", "Model railways"],
            0,
        ),
        (
            "What pattern characterizes products promoted on Richard Vobes's channel?",
            [
                "Folksy platform for grifters",
                "Neutral expert debates",
                "Rigorous scientific trials",
                "Consumer watchdog reviews",
            ],
            0,
        ),
        (
            "Why do 'cloud fake/real' claims fail?",
            [
                "Cloud physics doesn't care about vibes",
                "Clouds obey astrology",
                "Clouds require copper",
                "Clouds read blogs",
            ],
            0,
        ),
        (
            "What hard lesson do sovereign-citizen tactics ignore?",
            [
                "No paperwork beats reality",
                "Shortcut if crowds cheer",
                "Always film the meter",
                "Trust every pellet",
            ],
            0,
        ),
        (
            "Who ultimately pays for grifts promoted to conspiracy audiences?",
            [
                "The audience and their wallets",
                "The patent office",
                "Airline catering",
                "Town criers",
            ],
            0,
        ),
        (
            "What classic fallacy powers the suppression myth?",
            [
                "Appeal to persecution",
                "Appeal to nature",
                "Appeal to novelty",
                "Appeal to authority",
            ],
            0,
        ),
        (
            "What evidence standard should be applied to extraordinary claims?",
            [
                "Extraordinary claims need strong evidence",
                "Screenshots suffice",
                "Meters trump labs",
                "Humor trumps data",
            ],
            0,
        ),
        (
            "Why is 'wet-ink' obsession mocked?",
            [
                "Modern warrants are digital records",
                "Ink activates maritime law",
                "Ink holds royal DNA",
                "Ink unlocks juries",
            ],
            0,
        ),
        (
            "What's a practical way to evaluate 'too-good-to-be-true' products?",
            [
                "Be skeptical of magical fixes",
                "Film every cloud",
                "Refuse to register cars",
                "Shout at lampposts",
            ],
            0,
        ),
        (
            "What two things do scammers fear most?",
            [
                "Transparency and replication",
                "Crowds and clapping",
                "Rhymes and riddles",
                "Maps and timetables",
            ],
            0,
        ),
        (
            "Which habit helps avoid being scammed by conspiracy promoters?",
            [
                "Checking the boring details",
                "Skipping the footnotes",
                "Trusting the vibes",
                "Buying in bulk",
            ],
            0,
        ),
        (
            "What's a reliable sign you're looking at a grift?",
            [
                "Big promises, no mechanism",
                "Short videos only",
                "Too many footnotes",
                "Refusing interviews",
            ],
            0,
        ),
        (
            "What does 'freedom' often mean in these stories?",
            [
                "Freedom from paying and from blame",
                "Freedom to test hypotheses",
                "Freedom to hike hills",
                "Freedom to read papers",
            ],
            0,
        ),
    ]

    for i, (question, choices_text, correct_idx) in enumerate(data):
        # Reorder choices so correct answer is first
        reordered_choices = [choices_text[correct_idx]] + [
            choice for j, choice in enumerate(choices_text) if j != correct_idx
        ]
        puzzles.append(
            Puzzle(
                id=f"common_{i + 1:03d}",
                type="common_sense",
                question=question,
                choices=reordered_choices,
            )
        )

    # If fewer than 100 were defined, duplicate varied items with minor indexing
    # to ensure we supply 100 puzzles for first-time setup, without altering
    # semantics. Keep IDs unique.
    base_len = len(puzzles)
    if base_len < 100:
        for k in range(base_len, 100):
            src = puzzles[k % base_len]
            puzzles.append(
                Puzzle(
                    id=f"common_{k + 1:03d}",
                    type=src.type,
                    question=src.question,
                    choices=src.choices,
                )
            )
    elif base_len > 100:
        puzzles = puzzles[:100]

    return puzzles
