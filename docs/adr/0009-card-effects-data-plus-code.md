# Card effects: data for common effects, code for unique ones

Simple card effects (gain Resources, change Production, place a Tile, raise a Global Parameter) are listed as data on each card. Triggers, ongoing effects and unusual cards get their own Rust code.

Writing every card as code would repeat the same few effects across about 200 cards. Describing every card in a data-only effect language would force that language to grow until it covers every odd card, and interpreting it would cost speed (ADR 0004).
