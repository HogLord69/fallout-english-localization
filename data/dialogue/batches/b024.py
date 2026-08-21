# -*- coding: utf-8 -*-
# abradsne 506 is a real defect, not just a style problem: the line ended with a stray
# "]" followed by an untranslated Czech fragment ("A mas nejaky duvod drzet v ruce
# zbran?!") that would have been shown to the player verbatim. Removed.
# gcom6rea: the degree sign has no glyph in FONT2/3/4, so it had become "  degC" with a
# doubled space. Written as "deg C" with single spacing; the readout's indentation and
# CRLFs are preserved byte for byte.
GAME = "RES"
R = {
("abradsne.msg","506"):"You again? What do you want here? [His look hardens.] And have you got a reason to be holding a weapon?!",

("cmbatai2.msg","32021"):"Aaaargh!",

("gcom6rea.msg","1100"):"Thermal performance: 6000 MW\r\n                                        Electrical performance: 1900 MW\r\n                                    Steam production: 10200t/hour\r\n                                    Temperature: 318 deg C",
("gcom6rea.msg","1150"):"Thermal performance: 6000 MW\r\n                                        Electrical performance: 1900 MW\r\n                                    Steam production: 10200t/hour\r\n                                    Temperature: 1200 deg C... 1400 deg C... 1600 deg C",

("cfrancis.msg","20550"):"I'm the sheriff around here, and I haven't got time for you.",
("cfrancis.msg","20600"):"I already told you I'm busy. Still true.",

("ecbandit.msg","203"):"Everything valuable. On the ground. Now.",
("ecbandit.msg","207"):"No panic, now. It'll all be over in a minute.",
("ecbandit.msg","208"):"Let's see what we've got here.",
("ecbandit.msg","210"):"Don't make this hard on yourself.",
("ecbandit.msg","211"):"Hand it over.",
("ecbandit.msg","214"):"I promise I'll make it quick.",
("ecbandit.msg","215"):"Straight up to heaven with you.",

("misc.msg","50"):"Fallout needs the disc in the drive to run!",
}
