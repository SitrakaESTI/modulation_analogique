#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: BLU : émetteur (Hilbert / Hartley) et récepteur en simulation
# Author: Bloc 1 - simulations pédagogiques
# Description: Message -> filtre de Hilbert à 48 kHz (x + j.H{x}) -> rééchantillonneur -> BLU supérieure en bande de base -> FI -> bruit -> OL -> filtre passe-bande complexe 300-3000 Hz -> partie réelle
# GNU Radio version: 3.10.9.2

from gnuradio import analog
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import math




class ssb_tx_rx_sim_hl(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "BLU : émetteur (Hilbert / Hartley) et récepteur en simulation", catch_exceptions=True)

        ##################################################
        # Variables
        ##################################################
        self.interp = interp = 10
        self.audio_rate = audio_rate = 48000
        self.samp_rate = samp_rate = audio_rate*interp
        self.noise_amp = noise_amp = 0.0
        self.lo_phase = lo_phase = -2.5
        self.fm = fm = 1000
        self.fc = fc = 10e3

        ##################################################
        # Blocks
        ##################################################

        self.to_real = blocks.complex_to_real(1)
        self.throttle = blocks.throttle(gr.sizeof_float*1, audio_rate,True)
        self.spectre_fi_0 = blocks.vector_sink_c(1, 1024)
        self.spectre_emis_0 = blocks.vector_sink_f(1, 1024)
        self.spectre_bb_0 = blocks.vector_sink_c(1, 1024)
        self.sideband = filter.fir_filter_ccc(
            1,
            firdes.complex_band_pass(
                1,
                audio_rate,
                300,
                3000,
                200,
                window.WIN_HAMMING,
                6.76))
        self.scope_emis_1 = blocks.vector_sink_f(1, 1024)
        self.scope_emis_0 = blocks.vector_sink_f(1, 1024)
        self.scope_1 = blocks.vector_sink_f(1, 1024)
        self.scope_0 = blocks.vector_sink_f(1, 1024)
        self.resampler_c = filter.rational_resampler_ccf(
                interpolation=interp,
                decimation=1,
                taps=[],
                fractional_bw=0)
        self.resampler = filter.rational_resampler_fff(
                interpolation=interp,
                decimation=1,
                taps=[],
                fractional_bw=0)
        self.noise = analog.noise_source_c(analog.GR_GAUSSIAN, noise_amp, 0)
        self.msg_retarde = blocks.delay(gr.sizeof_float*1, 366)
        self.msg = analog.sig_source_f(audio_rate, analog.GR_COS_WAVE, fm, 1, 0, 0)
        self.mix_tx = blocks.multiply_vcc(1)
        self.mix_rx = blocks.multiply_vcc(1)
        self.lpf_rx = filter.fir_filter_ccf(
            interp,
            firdes.low_pass(
                1,
                samp_rate,
                5e3,
                2e3,
                window.WIN_HAMMING,
                6.76))
        self.lo_tx = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, fc, 1, 0, 0)
        self.lo_rx = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, (-fc), 1, 0, lo_phase)
        self.hilbert = filter.hilbert_fc(129, window.WIN_HAMMING, 6.76)
        self.emis_reel = blocks.complex_to_real(1)
        self.channel = blocks.add_vcc(1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.channel, 0), (self.mix_rx, 0))
        self.connect((self.channel, 0), (self.spectre_fi_0, 0))
        self.connect((self.emis_reel, 0), (self.scope_emis_0, 0))
        self.connect((self.emis_reel, 0), (self.spectre_emis_0, 0))
        self.connect((self.hilbert, 0), (self.resampler_c, 0))
        self.connect((self.lo_rx, 0), (self.mix_rx, 1))
        self.connect((self.lo_tx, 0), (self.mix_tx, 1))
        self.connect((self.lpf_rx, 0), (self.sideband, 0))
        self.connect((self.mix_rx, 0), (self.lpf_rx, 0))
        self.connect((self.mix_tx, 0), (self.channel, 0))
        self.connect((self.mix_tx, 0), (self.emis_reel, 0))
        self.connect((self.msg, 0), (self.throttle, 0))
        self.connect((self.msg_retarde, 0), (self.scope_0, 0))
        self.connect((self.noise, 0), (self.channel, 1))
        self.connect((self.resampler, 0), (self.scope_emis_1, 0))
        self.connect((self.resampler_c, 0), (self.mix_tx, 0))
        self.connect((self.sideband, 0), (self.spectre_bb_0, 0))
        self.connect((self.sideband, 0), (self.to_real, 0))
        self.connect((self.throttle, 0), (self.hilbert, 0))
        self.connect((self.throttle, 0), (self.msg_retarde, 0))
        self.connect((self.throttle, 0), (self.resampler, 0))
        self.connect((self.to_real, 0), (self.scope_1, 0))


    def get_interp(self):
        return self.interp

    def set_interp(self, interp):
        self.interp = interp
        self.set_samp_rate(self.audio_rate*self.interp)

    def get_audio_rate(self):
        return self.audio_rate

    def set_audio_rate(self, audio_rate):
        self.audio_rate = audio_rate
        self.set_samp_rate(self.audio_rate*self.interp)
        self.msg.set_sampling_freq(self.audio_rate)
        self.throttle.set_sample_rate(self.audio_rate)
        self.sideband.set_taps(firdes.complex_band_pass(1, self.audio_rate, 300, 3000, 200, window.WIN_HAMMING, 6.76))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.lo_tx.set_sampling_freq(self.samp_rate)
        self.lo_rx.set_sampling_freq(self.samp_rate)
        self.lpf_rx.set_taps(firdes.low_pass(1, self.samp_rate, 5e3, 2e3, window.WIN_HAMMING, 6.76))

    def get_noise_amp(self):
        return self.noise_amp

    def set_noise_amp(self, noise_amp):
        self.noise_amp = noise_amp
        self.noise.set_amplitude(self.noise_amp)

    def get_lo_phase(self):
        return self.lo_phase

    def set_lo_phase(self, lo_phase):
        self.lo_phase = lo_phase
        self.lo_rx.set_phase(self.lo_phase)

    def get_fm(self):
        return self.fm

    def set_fm(self, fm):
        self.fm = fm
        self.msg.set_frequency(self.fm)

    def get_fc(self):
        return self.fc

    def set_fc(self, fc):
        self.fc = fc
        self.lo_tx.set_frequency(self.fc)
        self.lo_rx.set_frequency((-self.fc))




def main(top_block_cls=ssb_tx_rx_sim_hl, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    tb.wait()


if __name__ == '__main__':
    main()
