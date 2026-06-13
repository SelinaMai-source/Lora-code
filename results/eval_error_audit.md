# Eval Error Audit

| run | debug_examples | strict_em | task_aware | top_error_type | router_mismatch_rate |
|---|---:|---:|---:|---|---:|
| `20260320_173808_seq_debug_local` | 0 | 0.0000 | 0.0000 |  | 0.0000 |
| `20260320_182331_citb_baselines` | 0 | 0.0000 | 0.0000 |  | 0.0000 |
| `20260407_213933_citb_ours_smoke_bosfix` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `20260407_214118_citb_ours_smoke_bosfix` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `20260407_214258_citb_ours_smoke_bosfix` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `baseline_alignment_single_segment` | 8 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `baseline_alignment_single_segment_round2` | 8 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `baseline_debug_audit` | 8 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `baseline_debug_audit_fast` | 8 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `baseline_main_seq_ep10_lr5e5` | 879 | 0.0102 | 0.0102 | unrelated_or_wrong | 0.0000 |
| `baseline_main_seq_greedy64` | 229 | 0.0044 | 0.0044 | unrelated_or_wrong | 0.0000 |
| `baseline_recovery_mini_seq` | 30 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `baseline_single_seg03_beam4_64_eoslearn` | 10 | 1.0000 | 1.0000 | strict_correct | 0.0000 |
| `baseline_single_seg03_beam4_64_eosmask` | 10 | 1.0000 | 1.0000 | strict_correct | 0.0000 |
| `baseline_single_seg03_greedy64_eosmask` | 10 | 0.9000 | 0.9000 | strict_correct | 0.0000 |
| `baseline_single_seg04_beam4_64_eosmask` | 10 | 0.7000 | 0.8000 | strict_correct | 0.0000 |
| `baseline_single_seg04_greedy64_eosmask` | 10 | 1.0000 | 1.0000 | strict_correct | 0.0000 |
| `baseline_transition_seg03_04_ctrl_ep5_lr2e4` | 30 | 0.3333 | 0.3333 | strict_correct | 0.0000 |
| `baseline_transition_seg03_04_ep10_lr5e5` | 30 | 0.9333 | 0.9333 | strict_correct | 0.0000 |
| `baseline_transition_seg03_04_ep8_lr1e4` | 30 | 0.9000 | 0.9000 | strict_correct | 0.0000 |
| `baseline_transition_seg03_04_ep8_lr1e4_eoslearn` | 30 | 0.5000 | 0.5000 | strict_correct | 0.0000 |
| `ours_main_full_ep10_lr5e5` | 579 | 0.0104 | 0.0104 | unrelated_or_wrong | 0.0000 |
| `ours_main_full_ep8_lr1e4` | 79 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_bank_no_router_s123` | 879 | 0.0046 | 0.0046 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_bank_no_router_s456` | 879 | 0.0034 | 0.0034 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_bank_no_router_s789` | 879 | 0.0023 | 0.0023 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_K100_s123_pilot` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_K50_s123_pilot` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_M128_s123_pilot` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_M256_s123_pilot` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_M64_s123_pilot` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_br4_s123_pilot` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_br8_s123_pilot` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_full_s123` | 879 | 0.0034 | 0.0034 | unrelated_or_wrong | 0.4528 |
| `paper_instrdialog_ours_full_s123_acl_overlap_active` | 40 | 0.0750 | 0.0750 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_full_s123_acl_overlap_forced` | 24 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.2917 |
| `paper_instrdialog_ours_full_s123_acl_overlap_train` | 60 | 0.1667 | 0.1667 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_full_s123_acl_validation` | 12 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_full_s123_pilot2_beta0` | 15 | 0.2000 | 0.2000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_full_s123_pilot2_default` | 15 | 0.2000 | 0.2000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_full_s123_pilot2_rw0` | 15 | 0.2000 | 0.2000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_full_s123_pilot2_thr010` | 15 | 0.2000 | 0.2000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_full_s123_pilot3_stress` | 275 | 0.1055 | 0.1527 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_full_s123_pilot3_stress_beta0_fix1` | 275 | 0.1455 | 0.1964 | unrelated_or_wrong | 0.1273 |
| `paper_instrdialog_ours_full_s123_pilot3_stress_fix1` | 275 | 0.1236 | 0.1818 | unrelated_or_wrong | 0.1127 |
| `paper_instrdialog_ours_full_s123_pilot3_stress_thr010_beta0_fix1` | 275 | 0.1709 | 0.2255 | unrelated_or_wrong | 0.1345 |
| `paper_instrdialog_ours_full_s123_pilot3_stress_thr010_fix1` | 275 | 0.1527 | 0.1964 | unrelated_or_wrong | 0.2000 |
| `paper_instrdialog_ours_full_s123_pilot4_routerfix` | 275 | 0.1418 | 0.1927 | unrelated_or_wrong | 0.1927 |
| `paper_instrdialog_ours_no_bank_s123` | 879 | 0.0034 | 0.0034 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_no_drift_s123` | 879 | 0.0023 | 0.0023 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_no_overlap_s123` | 879 | 0.0034 | 0.0034 | unrelated_or_wrong | 0.4562 |
| `paper_instrdialog_ours_no_overlap_s123_mini_abs_drift_routed` | 40 | 0.0250 | 0.0250 | unrelated_or_wrong | 0.5000 |
| `paper_instrdialog_ours_no_overlap_s123_mini_default` | 40 | 0.0750 | 0.0750 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_no_overlap_s123_mini_drift_aggressive` | 40 | 0.0500 | 0.0500 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_no_overlap_s123_mini_routed_oracle` | 40 | 0.0750 | 0.0750 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_no_overlap_s123_pilot4_routerfix` | 275 | 0.1673 | 0.2109 | unrelated_or_wrong | 0.1745 |
| `paper_instrdialog_ours_no_overlap_s123_pilot5_cachefix` | 275 | 0.1018 | 0.1455 | unrelated_or_wrong | 0.1636 |
| `paper_instrdialog_ours_no_overlap_s123_smoke_default` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_no_overlap_s123_smoke_drift_sensitive` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_no_overlap_s123_smoke_routed_oracle` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_no_router_s123` | 879 | 0.0057 | 0.0057 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_r16_s123_pilot` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_r32_s123_pilot` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_ours_r8_s123_pilot` | 6 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_periodic_latest_s123` | 879 | 0.0057 | 0.0057 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_periodic_latest_s456` | 879 | 0.0057 | 0.0057 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_periodic_latest_s789` | 879 | 0.0046 | 0.0068 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_replay_b10_s123` | 879 | 0.0023 | 0.0023 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_replay_b10_s456` | 879 | 0.0023 | 0.0023 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_replay_b10_s789` | 879 | 0.0011 | 0.0011 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_replay_b50_s123` | 879 | 0.0011 | 0.0011 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_replay_b50_s456` | 879 | 0.0023 | 0.0023 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_replay_b50_s789` | 879 | 0.0011 | 0.0011 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_router_only_s123` | 879 | 0.0023 | 0.0023 | unrelated_or_wrong | 0.2651 |
| `paper_instrdialog_router_only_s456` | 879 | 0.0034 | 0.0034 | unrelated_or_wrong | 0.2776 |
| `paper_instrdialog_router_only_s789` | 879 | 0.0034 | 0.0034 | unrelated_or_wrong | 0.2730 |
| `paper_instrdialog_seq_s123` | 879 | 0.0011 | 0.0011 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_seq_s456` | 879 | 0.0023 | 0.0023 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialog_seq_s789` | 879 | 0.0023 | 0.0023 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_bank_no_router_s123` | 1800 | 0.0589 | 0.1867 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_bank_no_router_s456` | 1800 | 0.0517 | 0.2622 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_bank_no_router_s789` | 1800 | 0.0356 | 0.2250 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_ours_full_s123` | 1800 | 0.0317 | 0.2322 | unrelated_or_wrong | 0.1517 |
| `paper_instrdialogpp_ours_full_s123_pilot3_stress_fix1` | 275 | 0.2655 | 0.3927 | unrelated_or_wrong | 0.3927 |
| `paper_instrdialogpp_ours_no_bank_s123` | 100 | 0.1500 | 0.3800 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_periodic_latest_s123` | 1800 | 0.0356 | 0.1922 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_periodic_latest_s456` | 1800 | 0.0378 | 0.2033 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_periodic_latest_s789` | 1800 | 0.0411 | 0.1789 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_replay_b10_s123` | 1800 | 0.0044 | 0.0789 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_replay_b10_s456` | 1800 | 0.0039 | 0.0611 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_replay_b10_s789` | 1800 | 0.0061 | 0.0639 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_replay_b50_s123` | 1800 | 0.0033 | 0.0894 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_replay_b50_s456` | 1150 | 0.0078 | 0.1191 | unrelated_or_wrong | 0.0000 |
| `paper_instrdialogpp_router_only_s123` | 1800 | 0.0156 | 0.2989 | unrelated_or_wrong | 0.1322 |
| `paper_instrdialogpp_seq_s123` | 1800 | 0.0106 | 0.0867 | unrelated_or_wrong | 0.0000 |
| `smoke` | 0 | 0.0000 | 0.0000 |  | 0.0000 |
| `smoke_anchor_drift` | 3 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `smoke_bosfix_bank_no_router` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `smoke_bosfix_ours_full` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `smoke_bosfix_ours_no_bank` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `smoke_bosfix_ours_no_drift` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `smoke_bosfix_ours_no_overlap` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `smoke_bosfix_ours_no_router` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `smoke_bosfix_periodic_multilora` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `smoke_bosfix_replay_lora` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `smoke_bosfix_router_only` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `smoke_bosfix_sequential_lora` | 15 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |
| `smoke_metrics_schema` | 3 | 0.0000 | 0.0000 | unrelated_or_wrong | 0.0000 |

## Representative Strict-EM Failures

- `20260407_213933_citb_ours_smoke_bosfix` seg=0 type=`unrelated_or_wrong` f1=0.179 gold=`Yeah, honestly, the more I think about it, the more I think it'll just be easier to wipe turkey off the map really quickly. I've done it in tourneys a few times before and it just makes everything simpler.` pred=`I think that's a good idea. I was thinking that if we can get rid of Russia, then we can split our fleets and take Turkey and England.`
- `20260407_213933_citb_ours_smoke_bosfix` seg=0 type=`empty_output` f1=0.000 gold=`Okay. Fair enough. One reason it might matter is because I could open with an aggressive attack on Austria if you want to blitz him quickly (e.g., DMZ Gal and then break it). Or you could organize a bounce in Gal and then not move there. On the other hand, if you’d prefer to take out Turkey first, I could go the standard Lepanto route. I’m happy to go either way, but I’d really like to coordinate with you if you’re game.

Maybe we both need a fuller picture of what is happening first. I’ll begin to reach out to others now.` pred=``
- `20260407_213933_citb_ours_smoke_bosfix` seg=0 type=`unrelated_or_wrong` f1=0.182 gold=`Well, here is a thought: any chance you would support my army to Greece?

If you’d like to work together against Austria, I think a great move would be to ask Austria to support you to Rum, and then support my army to Greece instead. 

If you are game to do that, I’d be happy to take down Austria with you and work with you moving forward. 

Thoughts?` pred=`Hey Austria, I was thinking that if Turkey and I were to work together, we could definitely take you down.`
- `20260407_213933_citb_ours_smoke_bosfix` seg=0 type=`unrelated_or_wrong` f1=0.054 gold=`But I appreciate that you also agreed to be “trio wires.” 🤣` pred=` thinking. I think we can both agree that the game is going to be won by the player who can get the most out of the board, and that means ta`
- `20260407_213933_citb_ours_smoke_bosfix` seg=0 type=`unrelated_or_wrong` f1=0.000 gold=`I'm starting to agree` pred=`I think we could definitely make a strong alliance. I've been thinking about how we can help each other out, and I think we could make some `
- `20260407_213933_citb_ours_smoke_bosfix` seg=1 type=`unrelated_or_wrong` f1=0.152 gold=`Yeah, honestly, the more I think about it, the more I think it'll just be easier to wipe turkey off the map really quickly. I've done it in tourneys a few times before and it just makes everything simpler.` pred=`I think that’s a good idea. I was thinking that if you and I can take out Turkey, then Germany can take England and France can take Germany.`
- `20260407_213933_citb_ours_smoke_bosfix` seg=1 type=`empty_output` f1=0.000 gold=`Okay. Fair enough. One reason it might matter is because I could open with an aggressive attack on Austria if you want to blitz him quickly (e.g., DMZ Gal and then break it). Or you could organize a bounce in Gal and then not move there. On the other hand, if you’d prefer to take out Turkey first, I could go the standard Lepanto route. I’m happy to go either way, but I’d really like to coordinate with you if you’re game.

Maybe we both need a fuller picture of what is happening first. I’ll begin to reach out to others now.` pred=``
- `20260407_213933_citb_ours_smoke_bosfix` seg=1 type=`unrelated_or_wrong` f1=0.195 gold=`Well, here is a thought: any chance you would support my army to Greece?

If you’d like to work together against Austria, I think a great move would be to ask Austria to support you to Rum, and then support my army to Greece instead. 

If you are game to do that, I’d be happy to take down Austria with you and work with you moving forward. 

Thoughts?` pred=`I think we can work together. I have a pretty good idea of what I want to do, but I need to know if you are interested in working with me. I`
- `20260407_213933_citb_ours_smoke_bosfix` seg=1 type=`unrelated_or_wrong` f1=0.063 gold=`But I appreciate that you also agreed to be “trio wires.” 🤣` pred=` thing. I think I have a few ideas, but I have to admit that I have a lot of respect for the way you play. I think you are one of the best p`
- `20260407_213933_citb_ours_smoke_bosfix` seg=1 type=`unrelated_or_wrong` f1=0.063 gold=`I'm starting to agree` pred=`I think we could do great things together. I'm not sure how much of a threat you are to the other two powers, but I think we could make a go`
- `20260407_213933_citb_ours_smoke_bosfix` seg=1 type=`partial_content_overlap` f1=0.556 gold=`Find the lyrics to the song "I Will Survive".` pred=`Find the song "I Will Survive" by Gloria Gaynor.`
- `20260407_213933_citb_ours_smoke_bosfix` seg=1 type=`unrelated_or_wrong` f1=0.000 gold=`I\'m looking for online mapping sites.` pred=`Find a map.`
- `20260407_213933_citb_ours_smoke_bosfix` seg=1 type=`partial_content_overlap` f1=0.615 gold=`Find information on hip fractures in the elderly.` pred=`Find information on hip fractures.`
- `20260407_213933_citb_ours_smoke_bosfix` seg=1 type=`unrelated_or_wrong` f1=0.000 gold=`Find tips, resources, supplies for getting organized and reducing clutter.` pred=`How can I get organised?`
- `20260407_213933_citb_ours_smoke_bosfix` seg=1 type=`partial_content_overlap` f1=0.500 gold=`Find the official legal rules and procedures pertaining to child support in Indiana.` pred=`Find information about child support in Indiana.`
- `20260407_214118_citb_ours_smoke_bosfix` seg=0 type=`unrelated_or_wrong` f1=0.164 gold=`Yeah, honestly, the more I think about it, the more I think it'll just be easier to wipe turkey off the map really quickly. I've done it in tourneys a few times before and it just makes everything simpler.` pred=`I think that's a good idea. I was thinking that if you and I can take out Turkey, then Germany can focus on England and we can all work toge`
- `20260407_214118_citb_ours_smoke_bosfix` seg=0 type=`empty_output` f1=0.000 gold=`Okay. Fair enough. One reason it might matter is because I could open with an aggressive attack on Austria if you want to blitz him quickly (e.g., DMZ Gal and then break it). Or you could organize a bounce in Gal and then not move there. On the other hand, if you’d prefer to take out Turkey first, I could go the standard Lepanto route. I’m happy to go either way, but I’d really like to coordinate with you if you’re game.

Maybe we both need a fuller picture of what is happening first. I’ll begin to reach out to others now.` pred=``
- `20260407_214118_citb_ours_smoke_bosfix` seg=0 type=`unrelated_or_wrong` f1=0.182 gold=`Well, here is a thought: any chance you would support my army to Greece?

If you’d like to work together against Austria, I think a great move would be to ask Austria to support you to Rum, and then support my army to Greece instead. 

If you are game to do that, I’d be happy to take down Austria with you and work with you moving forward. 

Thoughts?` pred=`Hey Austria, I was thinking that if Turkey and I were to work together, we could definitely take you down.`
- `20260407_214118_citb_ours_smoke_bosfix` seg=0 type=`unrelated_or_wrong` f1=0.055 gold=`But I appreciate that you also agreed to be “trio wires.” 🤣` pred=` thinking. I think we can both agree that the game is going to be won by the player who can get the most out of the board, and that means ta`
- `20260407_214118_citb_ours_smoke_bosfix` seg=0 type=`unrelated_or_wrong` f1=0.040 gold=`I'm starting to agree` pred=`I think we could make a great team. I've been thinking about how we can work together to take down the other powers. I think we should start`
