package com.skyfx.client;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.api.ClientModInitializer;

public class SkyFXClient implements ClientModInitializer {
	public static final String MOD_ID = "skyfx";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	@Override
	public void onInitializeClient() {
		LOGGER.info("SkyFX loaded");
	}
}
