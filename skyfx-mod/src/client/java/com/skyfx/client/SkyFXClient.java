package com.skyfx.client;

import com.mojang.blaze3d.platform.InputConstants;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.minecraft.client.KeyMapping;
import net.minecraft.resources.Identifier;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderEvents;
import net.fabricmc.loader.api.FabricLoader;

import com.skyfx.client.config.SkyFXConfig;
import com.skyfx.client.glint.GlintManager;
import com.skyfx.client.gui.SkyFXScreen;
import com.skyfx.client.render.AuraRenderer;

public class SkyFXClient implements ClientModInitializer {
	public static final String MOD_ID = "skyfx";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(Identifier.fromNamespaceAndPath(MOD_ID, "main"));
	private static KeyMapping openMenuKey;

	@Override
	public void onInitializeClient() {
		SkyFXConfig.load();
		FabricLoader.getInstance().getModContainer(MOD_ID).ifPresent(GlintManager::registerPacks);

		openMenuKey = KeyBindingHelper.registerKeyBinding(new KeyMapping("key.skyfx.open_menu", InputConstants.Type.KEYSYM, InputConstants.KEY_K, CATEGORY));
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (openMenuKey.consumeClick()) {
				if (client.screen == null) {
					client.setScreen(new SkyFXScreen(null));
				}
			}
		});

		WorldRenderEvents.BEFORE_BLOCK_OUTLINE.register(AuraRenderer::render);
		LOGGER.info("SkyFX loaded - press K in-game to open the menu");
	}
}
