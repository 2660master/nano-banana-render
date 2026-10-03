package com.skyfx.gametest;

import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

import com.skyfx.client.config.GlintType;
import com.skyfx.client.config.SkyFXConfig;
import com.skyfx.client.config.SkyType;
import com.skyfx.client.glint.GlintManager;
import com.skyfx.client.gui.SkyFXScreen;

/**
 * Boots the client, creates a flat test world and screenshots every SkyFX feature: the four skies, the vanilla and
 * palm glints on a held sword (with the item aura), the block aura in both styles and every tab of the menu.
 */
public class SkyFXClientGameTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext context) {
		// CI renders in software, keep the world small
		context.runOnClient(client -> {
			client.options.renderDistance().set(4);
			client.options.simulationDistance().set(5);
		});
		try (TestSingleplayerContext singleplayer = context.worldBuilder().create()) {
			context.getInput().resizeWindow(1280, 720);
			singleplayer.getClientWorld().waitForChunksRender();
			BlockPos feet = context.computeOnClient(client -> client.player.blockPosition());
			int x = feet.getX(), y = feet.getY(), z = feet.getZ();
			singleplayer.getServer().runCommand("time set 18000");
			singleplayer.getServer().runCommand(String.format("fill %d %d %d %d %d %d minecraft:grass_block", x - 2, y, z + 3, x + 2, y, z + 5));
			singleplayer.getServer().runCommand(String.format("setblock %d %d %d minecraft:diamond_block", x, y + 1, z + 3));
			singleplayer.getServer().runCommand(String.format("setblock %d %d %d minecraft:amethyst_block", x + 1, y + 1, z + 4));
			singleplayer.getServer().runCommand("give @a minecraft:diamond_sword");
			singleplayer.getServer().runCommand("enchant @a minecraft:sharpness 5");
			context.waitTicks(5);

			// skies, looking up across the horizon
			for (SkyType sky : SkyType.values()) {
				context.runOnClient(client -> {
					SkyFXConfig.get().sky = sky.id();
					look(client, 0.0F, -18.0F);
				});
				context.waitTicks(8);
				context.takeScreenshot("sky_" + sky.id());
				context.runOnClient(client -> look(client, 160.0F, -55.0F));
				context.waitTicks(3);
				context.takeScreenshot("sky_" + sky.id() + "_up");
			}

			// block aura on the diamond block, default colour and a custom colour
			context.runOnClient(client -> {
				SkyFXConfig.get().sky = SkyType.GALAXY.id();
				look(client, 0.0F, 32.0F);
			});
			context.waitTicks(5);
			context.takeScreenshot("aura_default");
			context.runOnClient(client -> SkyFXConfig.get().auraColor = 0xFF4D6D);
			context.waitTicks(3);
			context.takeScreenshot("aura_red");
			context.runOnClient(client -> {
				SkyFXConfig.get().auraStyle = 1;
				SkyFXConfig.get().auraColor = 0x9B6BFF;
			});
			context.waitTicks(3);
			context.takeScreenshot("aura_galaxy");

			// storm sea towards the giant moon and the pirate ship
			context.runOnClient(client -> {
				SkyFXConfig.get().sky = SkyType.STORM.id();
				look(client, 172.0F, -8.0F);
			});
			context.waitTicks(6);
			context.takeScreenshot("storm_moon_ship");

			// glints on the held sword
			context.runOnClient(client -> look(client, 0.0F, -10.0F));
			setGlint(context, GlintType.VANILLA);
			context.takeScreenshot("glint_vanilla");
			setGlint(context, GlintType.PALM);
			context.takeScreenshot("glint_palm");

			// item aura: a bold green outline, then the raw silhouette from the depth buffer (white = item)
			context.runOnClient(client -> {
				SkyFXConfig.get().itemAuraColor = 0x3CFF6E;
				SkyFXConfig.get().itemAuraWidth = 6;
			});
			context.waitTicks(3);
			context.takeScreenshot("item_aura_green");
			context.runOnClient(client -> System.setProperty("skyfx.debugItemMask", "true"));
			context.waitTicks(3);
			context.takeScreenshot("item_aura_mask");
			context.runOnClient(client -> {
				System.clearProperty("skyfx.debugItemMask");
				SkyFXConfig.get().itemAuraColor = 0xFF4FD8;
				SkyFXConfig.get().itemAuraWidth = 3;
			});

			// the menu, all three tabs
			context.runOnClient(client -> SkyFXConfig.get().sky = SkyType.AURORA.id());
			context.setScreen(() -> new SkyFXScreen(null));
			context.waitTicks(3);
			context.takeScreenshot("gui_skies");
			context.clickScreenButton("skyfx.tab.glints");
			context.waitTicks(3);
			context.takeScreenshot("gui_glints");
			context.clickScreenButton("skyfx.tab.aura");
			context.waitTicks(3);
			context.takeScreenshot("gui_aura");
			context.clickScreenButton("skyfx.tab.item_aura");
			context.waitTicks(3);
			context.takeScreenshot("gui_item_aura");
			context.setScreen(() -> null);
			context.waitTicks(2);
		}
	}

	private static void setGlint(ClientGameTestContext context, GlintType glint) {
		context.runOnClient(client -> GlintManager.apply(glint));
		context.waitTicks(2);
		context.waitFor(client -> client.getOverlay() == null, 20 * 60);
		context.waitTicks(10);
		if (context.computeOnClient(client -> GlintManager.current()) != glint) {
			throw new AssertionError("Glint " + glint + " was not applied");
		}
	}

	private static void look(Minecraft client, float yaw, float pitch) {
		if (client.player == null) return;
		client.player.setYRot(yaw);
		client.player.setXRot(pitch);
		client.player.yRotO = yaw;
		client.player.xRotO = pitch;
	}
}
